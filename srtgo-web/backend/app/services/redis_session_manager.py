"""
Redis-based Session Manager for sharing sessions between processes
Stores encrypted credentials in Redis for secure cross-process access
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import redis
from redis import Redis
import os
import sys

# Add srtgo modules to path
# Check if running in Docker (with /app/srtgo path)
if os.path.exists('/app/srtgo'):
    sys.path.append('/app')
else:
    # Local development path
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../..'))

# Apply ConnectionError patch before importing srtgo
try:
    from app.srtgo_wrapper.connection_error_patch import *
except Exception as e:
    print(f"Warning: Could not apply ConnectionError patch: {e}")

from app.services.crypto import encrypt_data, decrypt_data


class RedisSessionManager:
    """
    Manages active SRT/KTX sessions across processes using Redis
    Stores encrypted credentials that can be used by any worker
    """
    
    def __init__(self, redis_url: str = None, session_timeout_minutes: int = 30):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis_client: Redis = redis.from_url(self.redis_url)
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._local_cache: Dict[str, Any] = {}  # Local client cache
        
    def _get_redis_key(self, user_key: str) -> str:
        """Get Redis key for session data"""
        return f"session:{user_key}"
    
    def get_session(self, user_key: str) -> Optional[Any]:
        """
        Get active session client for a user
        First checks local cache, then Redis
        """
        # Check local cache first
        if user_key in self._local_cache:
            client = self._local_cache[user_key]
            if hasattr(client, 'is_login') and client.is_login:
                return client
            else:
                # Remove from cache if not logged in
                del self._local_cache[user_key]
        
        # Get credentials from Redis
        session_info = self.get_session_info(user_key)
        if not session_info:
            return None
        
        # Check if expired
        expires_str = session_info.get('expires')
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.utcnow() > expires:
                # Try to refresh
                if not self._refresh_session_in_redis(user_key):
                    self.remove_session(user_key)
                    return None
        
        # Create new client from stored credentials
        try:
            from app.srtgo_wrapper.srtgo_patch import patch_srtgo_modules
            patch_srtgo_modules()
            
            rail_type = session_info['rail_type']
            login_id = session_info['username']
            password = session_info['password']
            
            client = None
            if rail_type == "SRT":
                from srtgo.srt import SRT
                client = SRT(login_id, password, auto_login=True)
            elif rail_type == "KTX":
                from srtgo.ktx import Korail
                client = Korail(login_id, password, auto_login=True)
            
            if client and hasattr(client, 'is_login') and client.is_login:
                # Cache locally
                self._local_cache[user_key] = client
                # Update last accessed
                self._update_last_accessed(user_key)
                return client
                
        except Exception as e:
            print(f"Failed to create client from Redis session {user_key}: {e}")
            
        return None
    
    def create_session(self, user_key: str, rail_type: str, login_id: str, password: str) -> Optional[Any]:
        """
        Create a new session and store credentials in Redis
        """
        try:
            
            from app.srtgo_wrapper.srtgo_patch import patch_srtgo_modules
            patch_srtgo_modules()
            
            client = None
            rail_type = rail_type.upper()
            
            if rail_type == "SRT":
                from srtgo.srt import SRT
                print(f"DEBUG: Creating SRT client for {login_id}")
                client = SRT(login_id, password, auto_login=False)
                print(f"DEBUG: Attempting SRT login...")
                login_result = client.login()
                print(f"DEBUG: SRT login result: {login_result}")
                if not login_result:
                    print(f"ERROR: SRT login failed for {login_id}")
                    return None
                else:
                    print(f"SUCCESS: SRT login succeeded for {login_id}")
                    
            elif rail_type == "KTX":
                from srtgo.ktx import Korail
                print(f"DEBUG: Creating KTX client for {login_id}")
                client = Korail(login_id, password, auto_login=False)
                print(f"DEBUG: Attempting KTX login...")
                login_result = client.login()
                print(f"DEBUG: KTX login result: {login_result}")
                if not login_result:
                    print(f"ERROR: KTX login failed for {login_id}")
                    return None
                else:
                    print(f"SUCCESS: KTX login succeeded for {login_id}")
            else:
                return None
            
            # Store encrypted credentials in Redis
            session_data = {
                'rail_type': rail_type,
                'username': login_id,
                'password': encrypt_data(password),  # Encrypt password
                'created': datetime.utcnow().isoformat(),
                'expires': (datetime.utcnow() + self.session_timeout).isoformat(),
                'last_accessed': datetime.utcnow().isoformat(),
                'refresh_count': 0
            }
            
            redis_key = self._get_redis_key(user_key)
            self.redis_client.hset(redis_key, mapping=session_data)
            self.redis_client.expire(redis_key, int(self.session_timeout.total_seconds()))
            
            # Cache locally
            self._local_cache[user_key] = client
            
            print(f"Created Redis session for {user_key} ({rail_type})")
            return client
            
        except Exception as e:
            print(f"Failed to create session for {user_key}: {e}")
            return None
    
    def get_session_info(self, user_key: str) -> Optional[Dict[str, Any]]:
        """
        Get session information from Redis
        """
        try:
            redis_key = self._get_redis_key(user_key)
            data = self.redis_client.hgetall(redis_key)
            
            if not data:
                print(f"No Redis session found for {user_key}")
                return None
            
            # Decode bytes to strings and decrypt password
            session_info = {}
            for k, v in data.items():
                key = k.decode() if isinstance(k, bytes) else k
                value = v.decode() if isinstance(v, bytes) else v
                
                if key == 'password':
                    # Decrypt password
                    session_info[key] = decrypt_data(value)
                else:
                    session_info[key] = value
                    
            print(f"Found Redis session for {user_key}: rail_type={session_info.get('rail_type')}")
            return session_info
            
        except Exception as e:
            print(f"Error getting session info from Redis for {user_key}: {e}")
            return None
    
    def _update_last_accessed(self, user_key: str):
        """Update last accessed time in Redis"""
        try:
            redis_key = self._get_redis_key(user_key)
            self.redis_client.hset(redis_key, 'last_accessed', datetime.utcnow().isoformat())
        except:
            pass
    
    def _refresh_session_in_redis(self, user_key: str) -> bool:
        """Refresh session expiry in Redis"""
        try:
            redis_key = self._get_redis_key(user_key)
            new_expires = (datetime.utcnow() + self.session_timeout).isoformat()
            
            # Update expiry
            self.redis_client.hset(redis_key, 'expires', new_expires)
            self.redis_client.expire(redis_key, int(self.session_timeout.total_seconds()))
            
            # Increment refresh count
            current_count = int(self.redis_client.hget(redis_key, 'refresh_count') or 0)
            self.redis_client.hset(redis_key, 'refresh_count', current_count + 1)
            
            print(f"Refreshed Redis session for {user_key}")
            return True
            
        except Exception as e:
            print(f"Failed to refresh Redis session for {user_key}: {e}")
            return False
    
    def remove_session(self, user_key: str):
        """Remove session from Redis and local cache"""
        # Remove from local cache
        if user_key in self._local_cache:
            try:
                client = self._local_cache[user_key]
                if hasattr(client, 'logout'):
                    client.logout()
            except:
                pass
            del self._local_cache[user_key]
        
        # Remove from Redis
        try:
            redis_key = self._get_redis_key(user_key)
            self.redis_client.delete(redis_key)
            print(f"Removed Redis session for {user_key}")
        except Exception as e:
            print(f"Error removing Redis session for {user_key}: {e}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from Redis"""
        try:
            # Get all session keys
            pattern = self._get_redis_key("*")
            keys = list(self.redis_client.scan_iter(match=pattern))
            
            expired_count = 0
            for key in keys:
                data = self.redis_client.hget(key, 'expires')
                if data:
                    expires = datetime.fromisoformat(data.decode() if isinstance(data, bytes) else data)
                    if datetime.utcnow() > expires:
                        self.redis_client.delete(key)
                        expired_count += 1
                        
            if expired_count > 0:
                print(f"Cleaned up {expired_count} expired Redis sessions")
                
        except Exception as e:
            print(f"Error cleaning up expired sessions: {e}")


# Global Redis session manager instance
redis_session_manager = RedisSessionManager()