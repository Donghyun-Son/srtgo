"""
Session Manager for maintaining persistent login state
Manages SRT/KTX client instances and handles automatic re-login
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from threading import Lock
import sys
import os

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

class SessionManager:
    """
    Manages active SRT/KTX client sessions with automatic refresh
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        
    def get_session(self, user_key: str) -> Optional[Any]:
        """
        Get active session client for a user
        Returns None if session expired or doesn't exist
        """
        with self._lock:
            if user_key not in self._sessions:
                return None
                
            session_data = self._sessions[user_key]
            
            # Check if session expired
            if datetime.utcnow() > session_data['expires']:
                # Try to refresh the session
                if self._refresh_session(user_key):
                    return session_data['client']
                else:
                    # Remove expired session that couldn't be refreshed
                    del self._sessions[user_key]
                    return None
                    
            # Update last accessed time
            session_data['last_accessed'] = datetime.utcnow()
            return session_data['client']
    
    def create_session(self, user_key: str, rail_type: str, login_id: str, password: str) -> Optional[Any]:
        """
        Create a new session for a user
        Returns the client instance if successful, None otherwise
        """
        try:
            # Import after patching
            from app.srtgo_wrapper.srtgo_patch import patch_srtgo_modules
            patch_srtgo_modules()
            
            client = None
            rail_type = rail_type.upper()
            
            if rail_type == "SRT":
                from srtgo.srt import SRT
                client = SRT(login_id, password, auto_login=False)
                if not client.login():
                    return None
                    
            elif rail_type == "KTX":
                from srtgo.ktx import Korail
                client = Korail(login_id, password, auto_login=False)
                if not client.login():
                    return None
            else:
                return None
            
            # Store session data
            with self._lock:
                self._sessions[user_key] = {
                    'client': client,
                    'rail_type': rail_type,
                    'login_id': login_id,
                    'password': password,
                    'created': datetime.utcnow(),
                    'expires': datetime.utcnow() + self.session_timeout,
                    'last_accessed': datetime.utcnow(),
                    'refresh_count': 0
                }
                
            return client
            
        except Exception as e:
            print(f"Failed to create session for {user_key}: {e}")
            return None
    
    def _refresh_session(self, user_key: str) -> bool:
        """
        Refresh an expired session by re-logging in
        """
        if user_key not in self._sessions:
            return False
            
        session_data = self._sessions[user_key]
        
        try:
            client = session_data['client']
            rail_type = session_data['rail_type']
            
            # Check if already logged in
            if hasattr(client, 'is_login') and client.is_login:
                # Just extend the expiry
                session_data['expires'] = datetime.utcnow() + self.session_timeout
                return True
            
            # Re-login
            print(f"Refreshing session for {user_key} ({rail_type})")
            if client.login(session_data['login_id'], session_data['password']):
                session_data['expires'] = datetime.utcnow() + self.session_timeout
                session_data['refresh_count'] += 1
                print(f"Session refreshed successfully (count: {session_data['refresh_count']})")
                return True
            else:
                print(f"Failed to refresh session for {user_key}")
                return False
                
        except Exception as e:
            print(f"Error refreshing session for {user_key}: {e}")
            return False
    
    def get_session_info(self, user_key: str) -> Optional[Dict[str, Any]]:
        """
        Get session information (without the client object)
        Returns dict with username, password, rail_type, etc.
        """
        with self._lock:
            print(f"DEBUG: session_manager.get_session_info called with user_key={user_key}")
            print(f"DEBUG: Available sessions: {list(self._sessions.keys())}")
            
            if user_key in self._sessions:
                session_data = self._sessions[user_key]
                print(f"DEBUG: Found session for {user_key}")
                # Return safe session info (exclude the client object)
                return {
                    'username': session_data.get('login_id'),
                    'password': session_data.get('password'),
                    'rail_type': session_data.get('rail_type'),
                    'created': session_data.get('created'),
                    'expires': session_data.get('expires'),
                    'last_accessed': session_data.get('last_accessed'),
                    'refresh_count': session_data.get('refresh_count', 0)
                }
            else:
                print(f"DEBUG: No session found for {user_key}")
            return None
    
    def remove_session(self, user_key: str):
        """
        Remove a session (logout)
        """
        with self._lock:
            if user_key in self._sessions:
                try:
                    client = self._sessions[user_key]['client']
                    if hasattr(client, 'logout'):
                        client.logout()
                except:
                    pass
                del self._sessions[user_key]
    
    def cleanup_expired_sessions(self):
        """
        Remove all expired sessions
        """
        with self._lock:
            expired_keys = []
            for user_key, session_data in self._sessions.items():
                if datetime.utcnow() > session_data['expires']:
                    expired_keys.append(user_key)
                    
            for key in expired_keys:
                self.remove_session(key)
                
            if expired_keys:
                print(f"Cleaned up {len(expired_keys)} expired sessions")


# Global session manager instance
session_manager = SessionManager()