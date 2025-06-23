"""
Reservation Management Service
Implements reservation viewing, cancellation, and refund like the original CLI
"""
import asyncio
from typing import List, Dict, Any, Optional
from app.services.redis_session_manager import redis_session_manager
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
            client = redis_session_manager.get_session(user_key)
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
    
    def _make_serializable(self, obj: Any) -> Dict[str, Any]:
        """
        Convert object to JSON-serializable dictionary
        """
        try:
            import json
            
            # Try direct JSON serialization first
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # Object is not directly serializable, extract safe attributes
            safe_data = {}
            
            # Basic Python types that are JSON serializable
            safe_types = (str, int, float, bool, type(None))
            
            if hasattr(obj, '__dict__'):
                for key, value in obj.__dict__.items():
                    try:
                        if isinstance(value, safe_types):
                            safe_data[key] = value
                        elif isinstance(value, (list, tuple)):
                            # Handle lists/tuples recursively
                            safe_data[key] = [self._make_serializable(item) for item in value]
                        elif isinstance(value, dict):
                            # Handle dictionaries recursively  
                            safe_data[key] = {k: self._make_serializable(v) for k, v in value.items()}
                        else:
                            # For complex objects, try to convert to simple types
                            try:
                                # Test JSON serialization first
                                import json
                                json.dumps(value)
                                safe_data[key] = value
                            except (TypeError, ValueError):
                                # If not serializable, convert to string
                                safe_data[key] = str(value)
                    except Exception:
                        # If any error, just skip this attribute
                        continue
            else:
                # If no __dict__, just convert to string
                safe_data = {'__str__': str(obj)}
                
            return safe_data
    
    def _find_reservation_object(self, client, reservation_data: Dict[str, Any], rail_type: str):
        """
        Find the actual reservation object that matches the reservation data
        This is needed because cancel/refund methods expect the original library objects
        """
        try:
            # Get fresh reservation data
            if rail_type == "SRT":
                reservations = client.get_reservations()
                tickets = []  # SRT includes tickets in reservations
            else:  # KTX
                reservations = client.reservations()
                tickets = client.tickets()
            
            # Look for matching reservation in fresh data
            # Use unique_id and serializable_data to match, fallback to description
            target_unique_id = reservation_data.get('unique_id')
            target_serializable = reservation_data.get('serializable_data', {})
            target_description = reservation_data.get('description', '')
            
            # If no unique_id in reservation_data, try to extract from serializable_data or top-level
            if not target_unique_id:
                if rail_type == "SRT":
                    target_unique_id = target_serializable.get('reservation_number') or reservation_data.get('reservation_number')
                elif rail_type == "KTX":
                    target_unique_id = target_serializable.get('rsv_id') or target_serializable.get('pnr_no') or \
                                     reservation_data.get('rsv_id') or reservation_data.get('pnr_no')
            
            # Search in tickets first (paid items)
            for ticket in tickets:
                # Try unique ID matching first
                if target_unique_id and hasattr(ticket, 'pnr_no') and ticket.pnr_no == target_unique_id:
                    return ticket
                if target_unique_id and hasattr(ticket, 'rsv_id') and ticket.rsv_id == target_unique_id:
                    return ticket
                    
                # Fallback to description matching
                if str(ticket) == target_description:
                    return ticket
                    
                # Try serializable data matching for additional fields
                if hasattr(ticket, 'pnr_no') and target_serializable.get('pnr_no'):
                    if ticket.pnr_no == target_serializable.get('pnr_no'):
                        return ticket
            
            # Search in reservations
            for reservation in reservations:
                # Try unique ID matching first
                if target_unique_id:
                    if rail_type == "SRT" and hasattr(reservation, 'reservation_number'):
                        if reservation.reservation_number == target_unique_id:
                            return reservation
                    elif rail_type == "KTX" and hasattr(reservation, 'rsv_id'):
                        if reservation.rsv_id == target_unique_id:
                            return reservation
                
                # Fallback to description matching
                if str(reservation) == target_description:
                    return reservation
                    
                # Try serializable data matching for additional fields
                if rail_type == "SRT" and hasattr(reservation, 'reservation_number'):
                    if target_serializable.get('reservation_number') == reservation.reservation_number:
                        return reservation
                elif rail_type == "KTX" and hasattr(reservation, 'rsv_id'):
                    if target_serializable.get('rsv_id') == reservation.rsv_id:
                        return reservation
            
            return None
            
        except Exception as e:
            return None
    
    def cancel_reservation(self, 
                          user_key: str, 
                          rail_type: str, 
                          reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cancel a reservation or refund a ticket
        """
        try:
            # Get active session client
            client = redis_session_manager.get_session(user_key)
            if not client:
                return {
                    'success': False,
                    'error': 'No active session',
                    'message': '세션이 만료되었습니다. 다시 로그인해주세요.'
                }
            
            # Determine if this is a ticket (paid) or reservation (unpaid)
            is_ticket = reservation_data.get('is_ticket', False)
            rail_type = rail_type.upper()
            
            # Find the actual reservation object from current reservations
            actual_reservation = self._find_reservation_object(client, reservation_data, rail_type)
            if not actual_reservation:
                return {
                    'success': False,
                    'error': 'Reservation not found',
                    'message': '예약을 찾을 수 없습니다. 페이지를 새로고침 후 다시 시도해주세요.'
                }
            
            if is_ticket:
                # Refund ticket
                result = client.refund(actual_reservation)
                action = "환불"
            else:
                # Cancel reservation
                if rail_type == "SRT":
                    # SRT accepts either reservation object or reservation number
                    result = client.cancel(actual_reservation)
                else:
                    # KTX requires reservation object
                    result = client.cancel(actual_reservation)
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
            client = redis_session_manager.get_session(user_key)
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
            # Extract unique identifiers for better matching
            unique_id = None
            if rail_type == "SRT":
                unique_id = getattr(reservation, 'reservation_number', None)
            elif rail_type == "KTX":
                unique_id = getattr(reservation, 'rsv_id', None) or getattr(reservation, 'pnr_no', None)
            
            formatted = {
                'id': getattr(reservation, 'id', None),
                'unique_id': unique_id,
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
                'serializable_data': self._make_serializable(reservation)
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
                'serializable_data': self._make_serializable(reservation)
            }