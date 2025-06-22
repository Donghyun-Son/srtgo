import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoService:
    def __init__(self, secret_key: str):
        """Initialize crypto service with a secret key."""
        self.secret_key = secret_key.encode()
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance for encryption/decryption."""
        if self._fernet is None:
            # Use PBKDF2 to derive a key from the secret
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'srtgo_salt',  # Fixed salt for consistency
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result."""
        if not data:
            return ""
        
        encrypted = self._get_fernet().encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded encrypted data."""
        if not encrypted_data:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._get_fernet().decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception:
            # Return empty string if decryption fails
            return ""


# Global crypto service instance
_crypto_service: CryptoService = None


def get_crypto_service() -> CryptoService:
    """Get the global crypto service instance."""
    global _crypto_service
    if _crypto_service is None:
        from app.core.config import settings
        _crypto_service = CryptoService(settings.SECRET_KEY)
    return _crypto_service


def encrypt_password(password: str) -> str:
    """Encrypt a password."""
    return get_crypto_service().encrypt(password)


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a password."""
    return get_crypto_service().decrypt(encrypted_password)


def encrypt_data(data: str) -> str:
    """Encrypt any string data."""
    return get_crypto_service().encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt any string data."""
    return get_crypto_service().decrypt(encrypted_data)