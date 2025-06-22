"""
Telegram Notification Service
Implements telegram notifications like the original CLI
"""
import asyncio
from typing import Optional, Dict, Any
from app.models import UserSettings
from app.services.settings import SettingsService
from sqlmodel import Session


class TelegramService:
    """
    Telegram notification service for reservation updates
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.settings_service = SettingsService(session)
    
    async def send_reservation_success(self, 
                                     user_id: int, 
                                     rail_type: str, 
                                     reservation_info: Dict[str, Any]) -> bool:
        """
        Send reservation success notification to telegram
        """
        try:
            telegram_info = self._get_telegram_info(user_id, rail_type)
            if not telegram_info or not telegram_info['enabled']:
                return False
            
            # Format message like original CLI
            message = self._format_success_message(reservation_info, rail_type)
            
            return await self._send_message(
                telegram_info['token'], 
                telegram_info['chat_id'], 
                message
            )
            
        except Exception as e:
            print(f"Error sending telegram success notification: {e}")
            return False
    
    async def send_reservation_failure(self, 
                                     user_id: int, 
                                     rail_type: str, 
                                     error_message: str) -> bool:
        """
        Send reservation failure notification to telegram
        """
        try:
            telegram_info = self._get_telegram_info(user_id, rail_type)
            if not telegram_info or not telegram_info['enabled']:
                return False
            
            message = f"❌ 예약 실패\n\n{error_message}"
            
            return await self._send_message(
                telegram_info['token'], 
                telegram_info['chat_id'], 
                message
            )
            
        except Exception as e:
            print(f"Error sending telegram failure notification: {e}")
            return False
    
    async def send_reservation_error(self, 
                                   user_id: int, 
                                   rail_type: str, 
                                   error_message: str) -> bool:
        """
        Send reservation error notification to telegram
        """
        try:
            telegram_info = self._get_telegram_info(user_id, rail_type)
            if not telegram_info or not telegram_info['enabled']:
                return False
            
            message = f"⚠️ 예약 중 오류 발생\n\n{error_message}"
            
            return await self._send_message(
                telegram_info['token'], 
                telegram_info['chat_id'], 
                message
            )
            
        except Exception as e:
            print(f"Error sending telegram error notification: {e}")
            return False
    
    async def send_payment_success(self, 
                                 user_id: int, 
                                 rail_type: str, 
                                 payment_info: Dict[str, Any]) -> bool:
        """
        Send payment success notification to telegram
        """
        try:
            telegram_info = self._get_telegram_info(user_id, rail_type)
            if not telegram_info or not telegram_info['enabled']:
                return False
            
            message = f"💳 결제 완료\n\n카드: {payment_info.get('card_number_masked', 'N/A')}\n유형: {payment_info.get('business_type', 'N/A')}"
            
            return await self._send_message(
                telegram_info['token'], 
                telegram_info['chat_id'], 
                message
            )
            
        except Exception as e:
            print(f"Error sending telegram payment notification: {e}")
            return False
    
    def _get_telegram_info(self, user_id: int, rail_type: str) -> Optional[Dict[str, Any]]:
        """Get telegram configuration for user"""
        try:
            telegram_info = self.settings_service.get_decrypted_telegram_info(user_id, rail_type)
            if not telegram_info:
                return None
            
            return {
                'token': telegram_info['telegram_token'],
                'chat_id': telegram_info['telegram_chat_id'],
                'enabled': telegram_info['telegram_enabled']
            }
            
        except Exception as e:
            print(f"Error getting telegram info: {e}")
            return None
    
    def _format_success_message(self, reservation_info: Dict[str, Any], rail_type: str) -> str:
        """
        Format success message like original CLI
        """
        try:
            # Base success message
            message_lines = ["🎉 예약 성공! 🎉"]
            
            # Add train information
            if 'train_name' in reservation_info:
                message_lines.append(f"🚅 {reservation_info['train_name']}")
            
            # Add departure/arrival times if available
            if 'departure_time' in reservation_info and 'arrival_time' in reservation_info:
                message_lines.append(f"⏰ {reservation_info['departure_time']} → {reservation_info['arrival_time']}")
            
            # Add seat information
            if 'seat_info' in reservation_info and reservation_info['seat_info']:
                message_lines.append("\n🎫 좌석 정보:")
                for seat in reservation_info['seat_info']:
                    message_lines.append(f"  • {seat}")
            
            # Add payment status
            if reservation_info.get('payment_status') == 'completed':
                message_lines.append("\n💳 결제 완료")
            elif reservation_info.get('payment_status') == 'pending':
                message_lines.append("\n💳 결제 대기")
            
            return "\n".join(message_lines)
            
        except Exception as e:
            print(f"Error formatting success message: {e}")
            return f"🎉 예약 성공! 🎉\n\n{str(reservation_info)}"
    
    async def _send_message(self, token: str, chat_id: str, message: str) -> bool:
        """
        Send message to telegram using python-telegram-bot
        """
        try:
            import telegram
            
            bot = telegram.Bot(token)
            await bot.send_message(chat_id=chat_id, text=message)
            return True
            
        except Exception as e:
            print(f"Error sending telegram message: {e}")
            return False
    
    async def send_test_message(self, token: str, chat_id: str) -> Dict[str, Any]:
        """
        Send test message to validate telegram configuration
        """
        try:
            test_message = "🧪 SRTgo 웹 텔레그램 연결 테스트 메시지입니다."
            
            success = await self._send_message(token, chat_id, test_message)
            
            if success:
                return {
                    'success': True,
                    'message': '텔레그램 테스트 메시지 전송 성공'
                }
            else:
                return {
                    'success': False,
                    'message': '텔레그램 메시지 전송 실패'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'텔레그램 연결 오류: {str(e)}'
            }
    
    async def send_reservation_details(self, 
                                     user_id: int, 
                                     rail_type: str, 
                                     reservations: list) -> bool:
        """
        Send detailed reservation list to telegram (like original CLI)
        """
        try:
            telegram_info = self._get_telegram_info(user_id, rail_type)
            if not telegram_info or not telegram_info['enabled']:
                return False
            
            if not reservations:
                message = "📋 예매 내역이 없습니다."
            else:
                message_lines = ["📋 예매 내역"]
                for reservation in reservations:
                    message_lines.append(f"🚅 {reservation}")
                    # Add ticket details if available
                    if hasattr(reservation, 'tickets') and reservation.tickets:
                        for ticket in reservation.tickets:
                            message_lines.append(f"  🎫 {ticket}")
                message = "\n".join(message_lines)
            
            return await self._send_message(
                telegram_info['token'], 
                telegram_info['chat_id'], 
                message
            )
            
        except Exception as e:
            print(f"Error sending reservation details: {e}")
            return False