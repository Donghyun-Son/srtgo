"""
Payment Service for Auto-Payment Integration
Implements credit card payment functionality like the original CLI
"""
from typing import Optional, Dict, Any
from app.services.session_manager import session_manager
from app.models import UserSettings
from app.services.settings import SettingsService
from sqlmodel import Session


class PaymentService:
    """
    Payment service for automatic credit card payments
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.settings_service = SettingsService(session)
    
    def process_auto_payment(self, 
                           user_id: int, 
                           reservation: Any, 
                           rail_type: str) -> Dict[str, Any]:
        """
        Process automatic payment for a reservation
        Returns payment result with success status
        """
        try:
            # Get user's payment settings
            payment_info = self._get_payment_info(user_id, rail_type)
            if not payment_info:
                return {
                    'success': False,
                    'error': 'No payment information found',
                    'message': '결제 정보가 설정되지 않았습니다.'
                }
            
            # Get active session client
            user_key = f"{rail_type.lower()}_{payment_info['username']}"
            client = session_manager.get_session(user_key)
            if not client:
                return {
                    'success': False,
                    'error': 'No active session',
                    'message': '세션이 만료되었습니다. 다시 로그인해주세요.'
                }
            
            # Perform payment using original CLI logic
            result = self._execute_payment(client, reservation, payment_info)
            
            if result['success']:
                return {
                    'success': True,
                    'message': '💳 결제 성공! 💳',
                    'payment_info': result.get('payment_info', {})
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Payment failed'),
                    'message': f"결제 실패: {result.get('error', '알 수 없는 오류')}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'결제 처리 중 오류: {str(e)}'
            }
    
    def _get_payment_info(self, user_id: int, rail_type: str) -> Optional[Dict[str, Any]]:
        """Get decrypted payment information for user"""
        try:
            # Get user settings for the rail type
            settings = self.settings_service.get_settings_by_rail_type(user_id, rail_type)
            if not settings:
                return None
            
            # Check if auto payment is enabled
            if not settings.auto_payment:
                return None
                
            # Get decrypted card information
            if not all([settings.card_number, settings.card_password, 
                       settings.card_birthday, settings.card_expire]):
                return None
            
            # Decrypt card information
            card_info = self.settings_service.get_decrypted_card_info(user_id, rail_type)
            if not card_info:
                return None
            
            # Get credentials for username
            credentials = self.settings_service.get_decrypted_credentials(user_id, rail_type)
            if not credentials:
                return None
                
            return {
                'username': credentials['login_id'],
                'card_number': card_info['card_number'],
                'card_password': card_info['card_password'],
                'card_birthday': card_info['card_birthday'],
                'card_expire': card_info['card_expire']
            }
            
        except Exception as e:
            print(f"Error getting payment info: {e}")
            return None
    
    def _execute_payment(self, 
                        client: Any, 
                        reservation: Any, 
                        payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute payment using the original CLI pay_card logic
        """
        try:
            # Determine business registration type based on birthday length
            # 6 digits = 법인 사업자등록번호 (J), 10 digits = 개인 주민등록번호 (S)
            birthday = payment_info['card_birthday']
            business_type = "J" if len(birthday) == 6 else "S"
            
            # Call the original pay_with_card method
            success = client.pay_with_card(
                reservation,
                payment_info['card_number'],
                payment_info['card_password'], 
                birthday,
                payment_info['card_expire'],
                0,  # cvv (usually 0 for SRT/KTX)
                business_type
            )
            
            if success:
                return {
                    'success': True,
                    'payment_info': {
                        'card_number_masked': self._mask_card_number(payment_info['card_number']),
                        'business_type': '법인' if business_type == 'J' else '개인'
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Payment method returned False'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _mask_card_number(self, card_number: str) -> str:
        """Mask card number for security (show only last 4 digits)"""
        if len(card_number) >= 4:
            return '*' * (len(card_number) - 4) + card_number[-4:]
        return '*' * len(card_number)
    
    def validate_payment_settings(self, user_id: int, rail_type: str) -> Dict[str, Any]:
        """
        Validate if payment settings are properly configured
        """
        try:
            settings = self.settings_service.get_settings_by_rail_type(user_id, rail_type)
            if not settings:
                return {
                    'valid': False,
                    'message': '사용자 설정을 찾을 수 없습니다.'
                }
            
            if not settings.auto_payment:
                return {
                    'valid': False, 
                    'message': '자동 결제가 활성화되지 않았습니다.'
                }
            
            # Check required card fields
            missing_fields = []
            if not settings.card_number:
                missing_fields.append('카드번호')
            if not settings.card_password:
                missing_fields.append('카드비밀번호')
            if not settings.card_birthday:
                missing_fields.append('생년월일/사업자등록번호')
            if not settings.card_expire:
                missing_fields.append('카드유효기간')
            
            if missing_fields:
                return {
                    'valid': False,
                    'message': f'다음 정보가 누락되었습니다: {", ".join(missing_fields)}'
                }
            
            return {
                'valid': True,
                'message': '결제 설정이 완료되었습니다.'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'message': f'설정 확인 중 오류: {str(e)}'
            }