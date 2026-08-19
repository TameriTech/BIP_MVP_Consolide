from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class InsufficientFundsError(ConflictError):
    code = "insufficient_funds"


class InsufficientSharesError(ConflictError):
    code = "insufficient_shares"


class InstrumentNotTradableError(ConflictError):
    code = "instrument_not_tradable"


class KycNotValidatedError(ForbiddenError):
    code = "kyc_not_validated"


class AccountNotActiveError(ForbiddenError):
    code = "account_not_active"


class InvalidOrderStateError(ConflictError):
    code = "invalid_order_state"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )
