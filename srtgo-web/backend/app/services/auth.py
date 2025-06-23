from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select
from app.core.config import settings
from app.core.database import get_session
from app.models import User, UserCreate
from app.services.redis_session_manager import redis_session_manager as session_manager
import sys
import os

# Add the parent directory to the path to import srtgo modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../..'))

# Apply ConnectionError patch before importing srtgo
try:
    from app.srtgo_wrapper.connection_error_patch import *
except Exception as e:
    print(f"Warning: Could not apply ConnectionError patch: {e}")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, credentials: dict = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    
    # Note: Credentials are now stored in Redis via RedisSessionManager during login
    # No need for in-memory caching
    
    return encoded_jwt

def get_cached_credentials(user_key: str) -> Optional[dict]:
    """Get cached credentials for user from Redis session manager"""
    session_info = session_manager.get_session_info(user_key)
    if session_info:
        return {
            "login_id": session_info.get("username"),
            "password": session_info.get("password")
        }
    return None


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """Get user by username"""
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()


def authenticate_user_with_external(username: str, password: str, rail_type: str) -> bool:
    """Authenticate user with external SRT/KTX system and maintain session"""
    try:
        # 개발 환경에서 테스트 계정 허용
        if settings.DEBUG and username == "test" and password == "test":
            print(f"DEBUG: Allowing test account login for {rail_type}")
            return True
        
        # Create user key for session management
        user_key = f"{rail_type.lower()}_{username}"
        
        # Try to get existing session first
        client = session_manager.get_session(user_key)
        if client:
            print(f"Using existing session for {username} ({rail_type})")
            return True
        
        # Clear any corrupted session data before creating new one
        session_manager.remove_session(user_key)
        
        # Create new session
        client = session_manager.create_session(user_key, rail_type, username, password)
        if client:
            print(f"{rail_type} login successful for {username} - session created")
            return True
        else:
            print(f"{rail_type} login failed for {username}")
            return False
        
    except ImportError as e:
        print(f"Import error: {e}")
        # 개발 환경에서는 import 에러 시에도 테스트 계정 허용
        if settings.DEBUG and username == "test" and password == "test":
            print(f"DEBUG: Import error, but allowing test account")
            return True
        return False
    except Exception as e:
        print(f"Authentication error for {username}: {e}")
        # 개발 환경에서는 에러 시에도 테스트 계정 허용
        if settings.DEBUG and username == "test" and password == "test":
            print(f"DEBUG: Auth error, but allowing test account")
            return True
        return False


def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(session, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(session: Session, user: UserCreate) -> User:
    """Create a new user"""
    # Check if user already exists
    existing_user = get_user_by_username(session, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=user.is_active
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_key: str = payload.get("sub")  # This is like "srt_test" or "ktx_username"
        username: str = payload.get("username")
        rail_type: str = payload.get("rail_type")
        
        if user_key is None or username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # For SRT/KTX login, we don't store users in DB
    # Create a temporary user object from JWT data with rail_type info
    # Use a hash of username and rail_type as a unique ID
    import hashlib
    from datetime import datetime
    
    # Generate a unique ID based on username and rail_type
    unique_string = f"{rail_type}_{username}"
    user_id = int(hashlib.md5(unique_string.encode()).hexdigest()[:8], 16)
    
    user = User(
        id=user_id,
        username=username,
        email=f"{username}@{rail_type.lower() if rail_type else 'srt'}.com",
        hashed_password="",  # No password stored for external auth
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    # Store rail_type and user_key in the user object for access in routes
    # Use object.__setattr__ to bypass Pydantic validation
    object.__setattr__(user, 'rail_type', rail_type)
    object.__setattr__(user, 'user_key', user_key)  # Store the JWT user_key
    object.__setattr__(user, 'credentials', {'login_id': username, 'rail_type': rail_type})
    
    # Get session info if available
    session_info = session_manager.get_session_info(user_key)
    if session_info:
        object.__setattr__(user, 'session_info', session_info)
    
    return user


async def get_current_user_from_token(token: str, session: Session) -> Optional[User]:
    """Get current user from JWT token (for WebSocket)"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            return None
        return get_user_by_username(session, username)
    except JWTError:
        return None