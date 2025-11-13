"""Service for managing reservations and polling."""
import asyncio
import random
from typing import Dict, Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from json import JSONDecodeError

from backend.models.reservation import Reservation, ReservationStatus
from backend.models.credential import TrainCredential, TelegramCredential
from backend.services.train_service import TrainService
from backend.core.security import credential_encryption

# Import train errors for specific error handling
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from srtgo.srt import SRTError, SRTNetFunnelError
from srtgo.ktx import KorailError

# Polling interval configuration (same as original CLI)
RESERVE_INTERVAL_SHAPE = 4
RESERVE_INTERVAL_SCALE = 0.25
RESERVE_INTERVAL_MIN = 0.25


class ReservationService:
    """Service for reservation operations and background polling."""

    def __init__(self):
        """Initialize reservation service."""
        self.active_polls: Dict[int, asyncio.Task] = {}

    def _get_sleep_interval(self) -> float:
        """
        Get random sleep interval using gamma distribution.
        Same as original CLI implementation.
        """
        return random.gammavariate(RESERVE_INTERVAL_SHAPE, RESERVE_INTERVAL_SCALE) + RESERVE_INTERVAL_MIN

    async def _send_telegram_notification(self, db: AsyncSession, user_id: int, message: str):
        """
        Send telegram notification if enabled for user.
        Same as original CLI implementation.
        """
        try:
            # Get telegram credentials
            result = await db.execute(
                select(TelegramCredential).where(
                    TelegramCredential.user_id == user_id,
                    TelegramCredential.is_enabled == True
                )
            )
            telegram_cred = result.scalar_one_or_none()

            if not telegram_cred:
                return  # No telegram configured

            # Decrypt credentials
            token = credential_encryption.decrypt(telegram_cred.encrypted_token)
            chat_id = credential_encryption.decrypt(telegram_cred.encrypted_chat_id)

            # Send message via telegram
            try:
                import telegram
                bot = telegram.Bot(token=token)
                async with bot:
                    await bot.send_message(chat_id=chat_id, text=message)
            except Exception as e:
                print(f"Failed to send telegram message: {e}")

        except Exception as e:
            # Don't fail polling if telegram fails
            print(f"Telegram notification error: {e}")

    async def create_reservation(
        self,
        db: AsyncSession,
        user_id: int,
        reservation_data: Dict[str, Any]
    ) -> Reservation:
        """Create a new reservation."""
        reservation = Reservation(
            user_id=user_id,
            train_type=reservation_data['train_type'],
            departure_station=reservation_data['departure_station'],
            arrival_station=reservation_data['arrival_station'],
            departure_date=reservation_data['departure_date'],
            departure_time=reservation_data['departure_time'],
            passengers=reservation_data['passengers'],
            selected_trains=reservation_data.get('selected_trains'),
            seat_type=reservation_data.get('seat_type'),
            auto_payment=reservation_data.get('auto_payment', False),
            status=ReservationStatus.PENDING
        )

        db.add(reservation)
        await db.commit()
        await db.refresh(reservation)

        return reservation

    async def poll_for_availability(
        self,
        reservation_id: int,
        db: AsyncSession,
        callback: Optional[Callable] = None
    ):
        """
        Poll for train availability in background.

        This runs as a background task and updates reservation status.
        The polling continues even if the browser is closed, and results
        are saved to the database for later retrieval.
        """
        try:
            # Get reservation
            result = await db.execute(
                select(Reservation).where(Reservation.id == reservation_id)
            )
            reservation = result.scalar_one_or_none()

            if not reservation:
                return

            # Update status to searching
            reservation.status = ReservationStatus.SEARCHING
            await db.commit()

            # Get train credentials
            result = await db.execute(
                select(TrainCredential).where(
                    TrainCredential.user_id == reservation.user_id,
                    TrainCredential.train_type == reservation.train_type
                )
            )
            credential = result.scalar_one_or_none()

            if not credential:
                reservation.status = ReservationStatus.FAILED
                reservation.error_message = "Train credentials not found"
                await db.commit()
                return

            # Decrypt credentials
            user_id = credential_encryption.decrypt(credential.encrypted_user_id)
            password = credential_encryption.decrypt(credential.encrypted_password)

            # Initialize train service
            train_service = TrainService()
            success, message = await train_service.login(reservation.train_type, user_id, password)

            if not success:
                reservation.status = ReservationStatus.FAILED
                reservation.error_message = f"Login failed: {message}"
                await db.commit()
                return

            # Poll for availability for 24 hours (like original CLI behavior)
            max_duration = 24 * 3600  # 24 hours in seconds
            start_time = datetime.utcnow()
            attempt = 0

            print(f"[Polling #{reservation_id}] Started (max duration: 24 hours)")

            while True:
                # Check if 24 hours have passed
                elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
                if elapsed_seconds >= max_duration:
                    print(f"[Polling #{reservation_id}] TIMEOUT - 24 hours elapsed")
                    break

                try:
                    attempt += 1

                    # Refresh reservation to check if user cancelled
                    await db.refresh(reservation)
                    if reservation.status == ReservationStatus.CANCELLED:
                        print(f"[Polling #{reservation_id}] Cancelled by user")
                        return

                    # Search for trains
                    trains = await train_service.search_trains(
                        reservation.train_type,
                        reservation.departure_station,
                        reservation.arrival_station,
                        reservation.departure_date,
                        reservation.departure_time,
                        reservation.passengers
                    )

                    # Check if any selected trains are available
                    for train in trains:
                        train_number = str(getattr(train, 'train_number', getattr(train, 'train_no', '')))

                        # If no specific trains selected, try any available train
                        if not reservation.selected_trains or train_number in reservation.selected_trains:
                            # Check if seats are available (including standby) - same as CLI
                            if train_service.is_seat_available(train, reservation.train_type, reservation.seat_type):
                                # Try to reserve with seat type preference
                                reserve_success, reserve_obj, reserve_msg = await train_service.reserve_train(
                                    reservation.train_type,
                                    train,
                                    reservation.passengers,
                                    reservation.seat_type
                                )

                                if reserve_success:
                                    # Reservation successful
                                    is_waiting = hasattr(reserve_obj, 'is_waiting') and reserve_obj.is_waiting

                                    # Add tickets information to message (same as CLI)
                                    full_msg = reserve_msg
                                    if hasattr(reserve_obj, 'tickets') and reserve_obj.tickets:
                                        tickets_info = "\n" + "\n".join(map(str, reserve_obj.tickets))
                                        full_msg += tickets_info

                                    reservation.status = ReservationStatus.RESERVED
                                    reservation.result_data = {
                                        "train_number": train_number,
                                        "message": full_msg,
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "is_waiting": is_waiting
                                    }
                                    reservation.completed_at = datetime.utcnow()
                                    await db.commit()

                                    print(f"[Polling #{reservation_id}] SUCCESS - Reserved train {train_number}")

                                    # Auto payment if enabled and not waiting (same as CLI)
                                    payment_msg = ""
                                    if reservation.auto_payment and not is_waiting:
                                        # Get card credentials
                                        from backend.models.credential import CardCredential
                                        card_result = await db.execute(
                                            select(CardCredential).where(CardCredential.user_id == reservation.user_id)
                                        )
                                        card_cred = card_result.scalar_one_or_none()

                                        if card_cred:
                                            # Decrypt card info
                                            card_number = credential_encryption.decrypt(card_cred.encrypted_card_number)
                                            card_password = credential_encryption.decrypt(card_cred.encrypted_card_password)
                                            birthday = credential_encryption.decrypt(card_cred.encrypted_birthday)
                                            expire_date = credential_encryption.decrypt(card_cred.encrypted_expire_date)

                                            # Try to pay
                                            payment_success, payment_result = await train_service.pay_with_card(
                                                reservation.train_type,
                                                reserve_obj,
                                                card_number,
                                                card_password,
                                                birthday,
                                                expire_date
                                            )

                                            if payment_success:
                                                print(f"[Polling #{reservation_id}] Payment SUCCESS")
                                                payment_msg = "\n💳 결제 완료"
                                                reservation.result_data["payment"] = "completed"
                                            else:
                                                print(f"[Polling #{reservation_id}] Payment FAILED: {payment_result}")
                                                payment_msg = f"\n⚠️ 결제 실패: {payment_result}"
                                                reservation.result_data["payment"] = "failed"
                                                reservation.result_data["payment_error"] = payment_result
                                        else:
                                            print(f"[Polling #{reservation_id}] No card credentials found")
                                            payment_msg = "\n⚠️ 결제 정보 없음"
                                            reservation.result_data["payment"] = "no_card"

                                        await db.commit()

                                    # Send telegram notification (with tickets info, same as CLI)
                                    telegram_msg = f"🎉 예매 성공! 🎉\n\n열차번호: {train_number}\n{full_msg}{payment_msg}"
                                    await self._send_telegram_notification(db, reservation.user_id, telegram_msg)

                                    # Notify via callback if provided
                                    if callback:
                                        await callback(reservation_id, "success", reserve_obj)

                                    return

                    # No trains available, log progress and wait
                    elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()

                    # Log every 10 minutes
                    if int(elapsed_seconds) % 600 == 0 and attempt > 1:
                        hours = int(elapsed_seconds // 3600)
                        minutes = int((elapsed_seconds % 3600) // 60)
                        print(f"[Polling #{reservation_id}] Running for {hours}h {minutes}m ({attempt} attempts)")

                    if callback:
                        remaining_seconds = max_duration - elapsed_seconds
                        await callback(reservation_id, "polling", {
                            "attempt": attempt,
                            "elapsed_seconds": int(elapsed_seconds),
                            "remaining_seconds": int(remaining_seconds)
                        })

                    # Use gamma distribution for random interval (like original CLI)
                    await asyncio.sleep(self._get_sleep_interval())

                except SRTError as ex:
                    # Handle SRT-specific errors (same as original CLI)
                    msg = str(ex)
                    print(f"[Polling #{reservation_id}] SRTError at attempt {attempt}: {msg}")

                    if "정상적인 경로로 접근 부탁드립니다" in msg or isinstance(ex, SRTNetFunnelError):
                        # Clear netfunnel cache and retry
                        print(f"[Polling #{reservation_id}] Clearing netfunnel cache")
                        if callback:
                            await callback(reservation_id, "error", {
                                "type": "netfunnel",
                                "message": "네트워크 혼잡으로 캐시를 초기화하고 재시도합니다",
                                "original_error": msg,
                                "action": "retrying"
                            })
                        train_service.clear(reservation.train_type)
                        await asyncio.sleep(self._get_sleep_interval())
                        continue

                    elif "로그인 후 사용하십시오" in msg:
                        # Re-login and retry
                        print(f"[Polling #{reservation_id}] Session expired, re-logging in")
                        if callback:
                            await callback(reservation_id, "error", {
                                "type": "session_expired",
                                "message": "세션이 만료되어 재로그인 중입니다",
                                "action": "re_login"
                            })
                        success, login_msg = await train_service.login(reservation.train_type, user_id, password)
                        if not success:
                            # Re-login failed, stop polling
                            reservation.status = ReservationStatus.FAILED
                            reservation.error_message = f"Re-login failed: {login_msg}"
                            await db.commit()
                            print(f"[Polling #{reservation_id}] FAILED - Re-login failed")
                            if callback:
                                await callback(reservation_id, "error", {
                                    "type": "re_login_failed",
                                    "message": f"재로그인 실패: {login_msg}",
                                    "action": "stopped"
                                })
                            return
                        if callback:
                            await callback(reservation_id, "info", {
                                "message": "재로그인 성공, 예매 시도를 계속합니다"
                            })
                        await asyncio.sleep(self._get_sleep_interval())
                        continue

                    elif any(err in msg for err in [
                        "잔여석없음",
                        "사용자가 많아 접속이 원활하지 않습니다",
                        "예약대기 접수가 마감되었습니다",
                        "예약대기자한도수초과"
                    ]):
                        # Expected errors, just continue polling (no callback needed - this is normal)
                        await asyncio.sleep(self._get_sleep_interval())
                        continue

                    else:
                        # Unexpected SRT error, notify user and send telegram
                        print(f"[Polling #{reservation_id}] Unexpected SRTError, continuing: {msg}")
                        telegram_msg = f"[예약 #{reservation_id}] 예상치 못한 SRT 오류\n\n{msg}\n\n재시도 중입니다."
                        await self._send_telegram_notification(db, reservation.user_id, telegram_msg)
                        if callback:
                            await callback(reservation_id, "error", {
                                "type": "unexpected_srt_error",
                                "message": f"예상치 못한 오류 발생: {msg}",
                                "original_error": msg,
                                "action": "retrying"
                            })
                        await asyncio.sleep(self._get_sleep_interval())
                        continue

                except KorailError as ex:
                    # Handle Korail-specific errors (same as original CLI)
                    msg = str(ex)
                    print(f"[Polling #{reservation_id}] KorailError at attempt {attempt}: {msg}")

                    if "Need to Login" in msg:
                        # Re-login and retry
                        print(f"[Polling #{reservation_id}] Session expired, re-logging in")
                        if callback:
                            await callback(reservation_id, "error", {
                                "type": "session_expired",
                                "message": "세션이 만료되어 재로그인 중입니다",
                                "action": "re_login"
                            })
                        success, login_msg = await train_service.login(reservation.train_type, user_id, password)
                        if not success:
                            # Re-login failed, stop polling
                            reservation.status = ReservationStatus.FAILED
                            reservation.error_message = f"Re-login failed: {login_msg}"
                            await db.commit()
                            print(f"[Polling #{reservation_id}] FAILED - Re-login failed")
                            if callback:
                                await callback(reservation_id, "error", {
                                    "type": "re_login_failed",
                                    "message": f"재로그인 실패: {login_msg}",
                                    "action": "stopped"
                                })
                            return
                        if callback:
                            await callback(reservation_id, "info", {
                                "message": "재로그인 성공, 예매 시도를 계속합니다"
                            })
                        await asyncio.sleep(self._get_sleep_interval())
                        continue

                    elif any(err in msg for err in ["Sold out", "잔여석없음", "예약대기자한도수초과"]):
                        # Expected errors, just continue polling (no callback needed - this is normal)
                        await asyncio.sleep(self._get_sleep_interval())
                        continue

                    else:
                        # Unexpected Korail error, notify user and send telegram
                        print(f"[Polling #{reservation_id}] Unexpected KorailError, continuing: {msg}")
                        telegram_msg = f"[예약 #{reservation_id}] 예상치 못한 Korail 오류\n\n{msg}\n\n재시도 중입니다."
                        await self._send_telegram_notification(db, reservation.user_id, telegram_msg)
                        if callback:
                            await callback(reservation_id, "error", {
                                "type": "unexpected_korail_error",
                                "message": f"예상치 못한 오류 발생: {msg}",
                                "original_error": msg,
                                "action": "retrying"
                            })
                        await asyncio.sleep(self._get_sleep_interval())
                        continue

                except JSONDecodeError as ex:
                    # JSON decode error, just retry
                    print(f"[Polling #{reservation_id}] JSONDecodeError at attempt {attempt}, retrying")
                    if callback:
                        await callback(reservation_id, "error", {
                            "type": "json_decode_error",
                            "message": "응답 파싱 오류, 재시도 중입니다",
                            "action": "retrying"
                        })
                    await asyncio.sleep(self._get_sleep_interval())
                    continue

                except Exception as e:
                    # Generic error, notify user and send telegram
                    error_msg = str(e)
                    print(f"[Polling #{reservation_id}] Unexpected error at attempt {attempt}: {error_msg}")
                    telegram_msg = f"[예약 #{reservation_id}] 예상치 못한 오류\n\nType: {type(e).__name__}\nMessage: {error_msg}\n\n재시도 중입니다."
                    await self._send_telegram_notification(db, reservation.user_id, telegram_msg)
                    if callback:
                        await callback(reservation_id, "error", {
                            "type": "unexpected_error",
                            "message": f"예상치 못한 오류: {error_msg}",
                            "original_error": error_msg,
                            "action": "retrying"
                        })
                    await asyncio.sleep(self._get_sleep_interval())
                    continue

            # Timeout reached
            reservation.status = ReservationStatus.FAILED
            reservation.error_message = "No available trains found within 24 hours"
            await db.commit()

            print(f"[Polling #{reservation_id}] FAILED - Timeout (24 hours)")

            if callback:
                await callback(reservation_id, "failed", None)

        except Exception as e:
            # Update reservation with error
            print(f"[Polling #{reservation_id}] FATAL ERROR: {str(e)}")
            try:
                result = await db.execute(
                    select(Reservation).where(Reservation.id == reservation_id)
                )
                reservation = result.scalar_one_or_none()

                if reservation:
                    reservation.status = ReservationStatus.FAILED
                    reservation.error_message = str(e)
                    await db.commit()
            except Exception:
                pass

        finally:
            # Cleanup
            if reservation_id in self.active_polls:
                del self.active_polls[reservation_id]

    def start_polling(
        self,
        reservation_id: int,
        db: AsyncSession,
        callback: Optional[Callable] = None
    ):
        """Start background polling for a reservation."""
        task = asyncio.create_task(
            self.poll_for_availability(reservation_id, db, callback)
        )
        self.active_polls[reservation_id] = task
        return task

    def stop_polling(self, reservation_id: int):
        """Stop background polling for a reservation."""
        if reservation_id in self.active_polls:
            task = self.active_polls[reservation_id]
            task.cancel()
            del self.active_polls[reservation_id]

    def is_polling(self, reservation_id: int) -> bool:
        """Check if a reservation is currently being polled."""
        return reservation_id in self.active_polls


# Global instance
reservation_service = ReservationService()
