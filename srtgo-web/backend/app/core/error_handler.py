"""
Enhanced error handling with bot detection and session recovery
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Union
import logging

logger = logging.getLogger(__name__)

class SRTGoException(Exception):
    """Base exception for SRTgo errors"""
    def __init__(self, message: str, code: str = "SRTGO_ERROR", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class BotDetectedException(SRTGoException):
    """Raised when bot detection is triggered"""
    def __init__(self, message: str = "봇으로 감지되었습니다. 잠시 후 다시 시도해주세요."):
        super().__init__(message, "BOT_DETECTED", 429)

class SessionExpiredException(SRTGoException):
    """Raised when session is expired"""
    def __init__(self, message: str = "세션이 만료되었습니다. 다시 로그인해주세요."):
        super().__init__(message, "SESSION_EXPIRED", 401)

class CredentialsInvalidException(SRTGoException):
    """Raised when credentials are invalid"""
    def __init__(self, message: str = "로그인 정보가 올바르지 않습니다."):
        super().__init__(message, "INVALID_CREDENTIALS", 401)

async def srtgo_exception_handler(request: Request, exc: Union[SRTGoException, Exception]):
    """
    Handle SRTgo specific exceptions and common errors
    """
    if isinstance(exc, SRTGoException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "code": exc.code,
                "type": type(exc).__name__
            }
        )
    
    # Check for bot detection patterns in error messages
    error_message = str(exc)
    
    if "정상적인 경로로 접근" in error_message:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "봇으로 감지되었습니다. 잠시 후 다시 시도해주세요.",
                "code": "BOT_DETECTED",
                "type": "BotDetectedException"
            }
        )
    
    if "로그인 정보를 다시 확인" in error_message or "존재하지않는 회원" in error_message:
        return JSONResponse(
            status_code=401,
            content={
                "detail": "로그인 정보가 올바르지 않습니다.",
                "code": "INVALID_CREDENTIALS",
                "type": "CredentialsInvalidException"
            }
        )
    
    if "Your IP Address Blocked" in error_message:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "IP가 차단되었습니다. 잠시 후 다시 시도해주세요.",
                "code": "IP_BLOCKED",
                "type": "BotDetectedException"
            }
        )
    
    # Log unexpected errors
    logger.error(f"Unexpected error: {error_message}", exc_info=True)
    
    # Return generic error for unexpected cases
    return JSONResponse(
        status_code=500,
        content={
            "detail": "서버 오류가 발생했습니다.",
            "code": "INTERNAL_ERROR",
            "type": "InternalServerError"
        }
    )

def handle_srt_error(error_message: str):
    """
    Parse SRT/KTX error messages and raise appropriate exceptions
    """
    if "정상적인 경로로 접근" in error_message:
        raise BotDetectedException()
    
    if "로그인 정보를 다시 확인" in error_message or "존재하지않는 회원" in error_message:
        raise CredentialsInvalidException()
    
    if "Your IP Address Blocked" in error_message:
        raise BotDetectedException("IP가 차단되었습니다. 잠시 후 다시 시도해주세요.")
    
    # For other errors, raise generic exception
    raise SRTGoException(error_message)