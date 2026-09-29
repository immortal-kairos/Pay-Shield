from enum import Enum
from fastapi import Request, status
from fastapi.responses import JSONResponse

class ErrorCode(str, Enum):
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AMOUNT_EXCEEDS_CAP = "AMOUNT_EXCEEDS_CAP"
    UNSUPPORTED_CURRENCY = "UNSUPPORTED_CURRENCY"
    PAST_PAYMENT_DATE = "PAST_PAYMENT_DATE"
    INACTIVE_VENDOR = "INACTIVE_VENDOR"
    PAYMENT_NOT_FOUND = "PAYMENT_NOT_FOUND"
    TOTP_REQUIRED = "TOTP_REQUIRED"
    TOTP_INVALID = "TOTP_INVALID"
    SELF_APPROVAL_NOT_ALLOWED = "SELF_APPROVAL_NOT_ALLOWED"
    PAYMENT_NOT_REVIEWABLE = "PAYMENT_NOT_REVIEWABLE"
    BANK_DETAILS_IMMUTABLE = "BANK_DETAILS_IMMUTABLE"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"
    EXPORT_FILE_NOT_FOUND = "EXPORT_FILE_NOT_FOUND"
    # US-14
    INVALID_EXPORT_TYPE = "INVALID_EXPORT_TYPE"
    INVALID_FREQUENCY = "INVALID_FREQUENCY"
    EMPTY_RECIPIENT_LIST = "EMPTY_RECIPIENT_LIST"
    REPORT_SCHEDULE_NOT_FOUND = "REPORT_SCHEDULE_NOT_FOUND"
    # --- NEW BULK ERROR CODES ---
    EMPTY_BULK_SELECTION = "EMPTY_BULK_SELECTION"
    BULK_LIMIT_EXCEEDED = "BULK_LIMIT_EXCEEDED"


class PayShieldError(Exception):
    def __init__(self, status_code: int, error: ErrorCode, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message

async def payshield_error_handler(request: Request, exc: PayShieldError):
    error_val = exc.error.value if hasattr(exc.error, 'value') else exc.error
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_val, "message": exc.message},
    )

async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."},
    )