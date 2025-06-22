"""
Reservation Management Service
Implements reservation viewing, cancellation, and refund like the original CLI
"""
import asyncio
from typing import List, Dict, Any, Optional
from app.services.session_manager import session_manager
from app.services.telegram_service import TelegramService
from sqlmodel import Session


class ReservationManagementService:
    """
    Service for managing existing reservations and tickets
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.telegram_service = TelegramService(session)
    
    def get_all_reservations(self, user_key: str, rail_type: str) -> Dict[str, Any]:
        """
        Get all reservations and tickets for a user like original CLI
        """
        try:
            # Get active session client
            client = session_manager.get_session(user_key)
            if not client:
                return {
                    'success': False,
                    'error': 'No active session',
                    'message': '세션이 만료되었습니다. 다시 로그인해주세요.'
                }
            
            rail_type = rail_type.upper()
            
            # Get reservations and tickets based on rail type
            if rail_type == "SRT":
                reservations = client.get_reservations()
                tickets = []  # SRT tickets are included in reservations
            else:  # KTX
                reservations = client.reservations()
                tickets = client.tickets()
            
            # Combine and format reservations
            all_reservations = self._format_reservations(reservations, tickets, rail_type)
            
            return {
                'success': True,
                'reservations': all_reservations,
                'count': len(all_reservations)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'예약 조회 중 오류: {str(e)}'
            }
    
    def cancel_reservation(self, 
                          user_key: str, 
                          rail_type: str, 
                          reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cancel a reservation or refund a ticket
        """
        try:
            # Get active session client
            client = session_manager.get_session(user_key)
            if not client:
                return {
                    'success': False,
                    'error': 'No active session',
                    'message': '세션이 만료되었습니다. 다시 로그인해주세요.'
                }
            
            # Determine if this is a ticket (paid) or reservation (unpaid)
            is_ticket = reservation_data.get('is_ticket', False)
            
            if is_ticket:
                # Refund ticket
                result = client.refund(reservation_data)
                action = "환불"
            else:
                # Cancel reservation
                result = client.cancel(reservation_data)
                action = "취소"
            
            if result:
                return {
                    'success': True,
                    'message': f'예약 {action}이 완료되었습니다.',
                    'action': action
                }
            else:
                return {
                    'success': False,
                    'message': f'예약 {action}에 실패했습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'예약 처리 중 오류: {str(e)}'
            }
    
    def pay_reservation(self, 
                       user_key: str, 
                       rail_type: str, 
                       reservation_data: Dict[str, Any],
                       user_id: int) -> Dict[str, Any]:
        """
        Pay for an unpaid reservation
        """
        try:
            # Get active session client
            client = session_manager.get_session(user_key)
            if not client:
                return {
                    'success': False,
                    'error': 'No active session',
                    'message': '세션이 만료되었습니다. 다시 로그인해주세요.'
                }
            
            # Use payment service to process payment
            from app.services.payment_service import PaymentService
            payment_service = PaymentService(self.session)
            
            result = payment_service.process_auto_payment(user_id, reservation_data, rail_type)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'결제 처리 중 오류: {str(e)}'
            }
    
    async def send_reservations_to_telegram(self, 
                                          user_id: int, 
                                          rail_type: str, 
                                          reservations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send reservation details to telegram like original CLI
        """
        try:
            success = await self.telegram_service.send_reservation_details(
                user_id, 
                rail_type, 
                reservations
            )
            
            if success:
                return {
                    'success': True,
                    'message': '텔레그램으로 예매 정보를 전송했습니다.'
                }
            else:
                return {
                    'success': False,
                    'message': '텔레그램 전송에 실패했습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'텔레그램 전송 중 오류: {str(e)}'
            }
    
    def _format_reservations(self, 
                           reservations: List[Any], 
                           tickets: List[Any], 
                           rail_type: str) -> List[Dict[str, Any]]:
        """
        Format reservations and tickets for API response
        """
        all_reservations = []
        
        # Add tickets (paid reservations)
        for ticket in tickets:
            formatted = self._format_single_reservation(ticket, True, rail_type)
            all_reservations.append(formatted)
        
        # Add reservations (may be paid or unpaid)
        for reservation in reservations:
            is_ticket = hasattr(reservation, "paid") and reservation.paid
            formatted = self._format_single_reservation(reservation, is_ticket, rail_type)
            all_reservations.append(formatted)
        
        return all_reservations
    
    def _format_single_reservation(self, 
                                 reservation: Any, 
                                 is_ticket: bool, 
                                 rail_type: str) -> Dict[str, Any]:
        """
        Format a single reservation/ticket for API response
        """
        try:
            formatted = {
                'id': getattr(reservation, 'id', None),
                'is_ticket': is_ticket,
                'status': 'paid' if is_ticket else 'unpaid',
                'rail_type': rail_type,
                'description': str(reservation),
                'departure_time': getattr(reservation, 'departure_time', None),
                'arrival_time': getattr(reservation, 'arrival_time', None),
                'departure_station': getattr(reservation, 'departure_station', None),
                'arrival_station': getattr(reservation, 'arrival_station', None),
                'train_name': getattr(reservation, 'train_name', None),
                'train_no': getattr(reservation, 'train_no', None),
                'price': getattr(reservation, 'price', None),
                'passenger_count': getattr(reservation, 'passenger_count', None),
                'seat_info': [],
                'raw_data': reservation  # Store raw object for operations
            }
            
            # Add ticket details if available
            if hasattr(reservation, 'tickets') and reservation.tickets:
                for ticket in reservation.tickets:
                    formatted['seat_info'].append({
                        'description': str(ticket),
                        'car': getattr(ticket, 'car', None),
                        'seat': getattr(ticket, 'seat', None),
                        'seat_type': getattr(ticket, 'seat_type', None)
                    })
            
            return formatted
            
        except Exception as e:
            # Return basic info if formatting fails
            return {
                'id': None,
                'is_ticket': is_ticket,
                'status': 'paid' if is_ticket else 'unpaid',
                'rail_type': rail_type,
                'description': str(reservation),
                'error': f'Formatting error: {str(e)}',
                'raw_data': reservation
            }