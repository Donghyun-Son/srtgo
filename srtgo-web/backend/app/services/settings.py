from typing import Optional, List
from sqlmodel import Session, select
from app.models import User, UserSettings, UserSettingsCreate, UserSettingsUpdate
from app.services.crypto import encrypt_password, decrypt_password


class SettingsService:
    """Service for managing user settings with encryption."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_user_settings(self, user_id: int) -> List[UserSettings]:
        """Get all settings for a user."""
        statement = select(UserSettings).where(UserSettings.user_id == user_id)
        return list(self.session.exec(statement).all())
    
    def get_settings_by_rail_type(self, user_id: int, rail_type: str) -> Optional[UserSettings]:
        """Get settings for specific rail type."""
        statement = select(UserSettings).where(
            UserSettings.user_id == user_id,
            UserSettings.rail_type == rail_type
        )
        return self.session.exec(statement).first()
    
    def create_settings(self, user_id: int, settings_data: UserSettingsCreate) -> UserSettings:
        """Create new user settings with encryption."""
        settings_data.user_id = user_id
        
        # Encrypt sensitive data
        if settings_data.encrypted_password:
            settings_data.encrypted_password = encrypt_password(settings_data.encrypted_password)
        if settings_data.card_number:
            settings_data.card_number = encrypt_password(settings_data.card_number)
        if settings_data.card_password:
            settings_data.card_password = encrypt_password(settings_data.card_password)
        if settings_data.card_birthday:
            settings_data.card_birthday = encrypt_password(settings_data.card_birthday)
        if settings_data.card_expire:
            settings_data.card_expire = encrypt_password(settings_data.card_expire)
        if settings_data.telegram_token:
            settings_data.telegram_token = encrypt_password(settings_data.telegram_token)
        
        db_settings = UserSettings.model_validate(settings_data)
        self.session.add(db_settings)
        self.session.commit()
        self.session.refresh(db_settings)
        return db_settings
    
    def update_settings(self, user_id: int, settings_id: int, settings_update: UserSettingsUpdate) -> Optional[UserSettings]:
        """Update user settings with encryption."""
        statement = select(UserSettings).where(
            UserSettings.id == settings_id,
            UserSettings.user_id == user_id
        )
        db_settings = self.session.exec(statement).first()
        if not db_settings:
            return None
        
        # Get update data and encrypt sensitive fields
        settings_data = settings_update.model_dump(exclude_unset=True)
        
        if "encrypted_password" in settings_data and settings_data["encrypted_password"]:
            settings_data["encrypted_password"] = encrypt_password(settings_data["encrypted_password"])
        if "card_number" in settings_data and settings_data["card_number"]:
            settings_data["card_number"] = encrypt_password(settings_data["card_number"])
        if "card_password" in settings_data and settings_data["card_password"]:
            settings_data["card_password"] = encrypt_password(settings_data["card_password"])
        if "card_birthday" in settings_data and settings_data["card_birthday"]:
            settings_data["card_birthday"] = encrypt_password(settings_data["card_birthday"])
        if "card_expire" in settings_data and settings_data["card_expire"]:
            settings_data["card_expire"] = encrypt_password(settings_data["card_expire"])
        if "telegram_token" in settings_data and settings_data["telegram_token"]:
            settings_data["telegram_token"] = encrypt_password(settings_data["telegram_token"])
        
        for key, value in settings_data.items():
            setattr(db_settings, key, value)
        
        self.session.add(db_settings)
        self.session.commit()
        self.session.refresh(db_settings)
        return db_settings
    
    def delete_settings(self, user_id: int, settings_id: int) -> bool:
        """Delete user settings."""
        statement = select(UserSettings).where(
            UserSettings.id == settings_id,
            UserSettings.user_id == user_id
        )
        db_settings = self.session.exec(statement).first()
        if not db_settings:
            return False
        
        self.session.delete(db_settings)
        self.session.commit()
        return True
    
    def get_decrypted_credentials(self, user_id: int, rail_type: str) -> Optional[dict]:
        """Get decrypted login credentials for a rail type."""
        settings = self.get_settings_by_rail_type(user_id, rail_type)
        if not settings or not settings.login_id or not settings.encrypted_password:
            return None
        
        return {
            "login_id": settings.login_id,
            "password": decrypt_password(settings.encrypted_password)
        }
    
    def get_decrypted_card_info(self, user_id: int, rail_type: str) -> Optional[dict]:
        """Get decrypted card information for a rail type."""
        settings = self.get_settings_by_rail_type(user_id, rail_type)
        if not settings:
            return None
        
        return {
            "card_number": decrypt_password(settings.card_number) if settings.card_number else None,
            "card_password": decrypt_password(settings.card_password) if settings.card_password else None,
            "card_birthday": decrypt_password(settings.card_birthday) if settings.card_birthday else None,
            "card_expire": decrypt_password(settings.card_expire) if settings.card_expire else None,
            "auto_payment": settings.auto_payment
        }
    
    def get_decrypted_telegram_info(self, user_id: int, rail_type: str) -> Optional[dict]:
        """Get decrypted telegram information for a rail type."""
        settings = self.get_settings_by_rail_type(user_id, rail_type)
        if not settings:
            return None
        
        return {
            "telegram_token": decrypt_password(settings.telegram_token) if settings.telegram_token else None,
            "telegram_chat_id": settings.telegram_chat_id,
            "telegram_enabled": settings.telegram_enabled
        }