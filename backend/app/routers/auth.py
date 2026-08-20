from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
    UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: DbSession):
    _, tokens = auth_service.register_user(db, data)
    return tokens


@router.post("/login", response_model=TokenPair)
def login(data: LoginRequest, db: DbSession):
    _, tokens = auth_service.authenticate_user(db, data.email, data.password)
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: DbSession):
    return auth_service.refresh_tokens(db, data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # Stateless JWT — nothing to invalidate server-side for the MVP.
    # The client is responsible for discarding both tokens.
    return None


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(data: ChangePasswordRequest, db: DbSession, user: CurrentUser):
    auth_service.change_password(db, user, data.current_password, data.new_password)
    return None


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: DbSession):
    token = auth_service.request_password_reset(db, data.email)
    return ForgotPasswordResponse(
        message="If an account exists for this email, a password reset link has been issued.",
        reset_token=token,
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(data: ResetPasswordRequest, db: DbSession):
    auth_service.reset_password(db, data.token, data.new_password)
    return None


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
