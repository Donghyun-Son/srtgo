from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session
from app.core.database import get_session
from app.models import User, UserCreate, UserRead
from app.services.auth import authenticate_user, authenticate_user_with_external, create_access_token, get_current_user, create_user

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


@router.post("/register", response_model=UserRead)
def register(user: UserCreate, session: Session = Depends(get_session)):
    """Register a new user"""
    return create_user(session, user)


@router.post("/token")
def login(
    username: str = Form(),
    password: str = Form(),
    rail_type: str = Form(),
    session: Session = Depends(get_session)
):
    """Login with SRT/KTX credentials and get access token"""
    import logging
    logger = logging.getLogger(__name__)
    
    print(f"=== LOGIN ENDPOINT CALLED ===")
    print(f"Username: {username}")
    print(f"Rail type: {rail_type}")
    
    logger.info(f"Login attempt for user: {username}, rail_type: {rail_type}")
    
    # Authenticate with external SRT/KTX system
    if not authenticate_user_with_external(username, password, rail_type):
        logger.error(f"Failed to authenticate user {username} with {rail_type}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SRT/KTX 로그인 실패. 아이디와 비밀번호를 확인해주세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Successfully authenticated user {username} with {rail_type}")
    
    # Create a unique user identifier with rail type
    user_key = f"{rail_type.lower()}_{username}"
    
    # Generate user_id using the same method as get_current_user
    import hashlib
    unique_string = f"{rail_type.upper()}_{username}"
    user_id = int(hashlib.md5(unique_string.encode()).hexdigest()[:8], 16)
    
    # Store session in Redis for cross-process access
    from app.services.redis_session_manager import redis_session_manager
    session_client = redis_session_manager.create_session(
        user_key=user_key,
        rail_type=rail_type.upper(),
        login_id=username,
        password=password
    )
    
    if not session_client:
        logger.error(f"Failed to create Redis session for {username}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 생성에 실패했습니다."
        )
    
    logger.info(f"Created Redis session for {username}")
    
    # Create access token with user information and cache credentials
    access_token = create_access_token(
        data={
            "sub": user_key,
            "username": username,
            "rail_type": rail_type.upper(),
            "user_id": user_id
        },
        credentials={
            "login_id": username,
            "password": password,
            "rail_type": rail_type.upper()
        }
    )
    
    logger.info(f"Token created for user {username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user