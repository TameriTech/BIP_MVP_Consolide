import uuid

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import RoleEnum


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    # MVP simulation: no outbound email integration exists, so the reset
    # token is handed back directly instead of being emailed (same
    # simulated-not-real-infra approach used for KYC). Only populated when
    # the email matches an account, but the `message` above is always
    # identical either way so the endpoint can't be used to enumerate
    # registered emails from the response *shape* alone.
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    role: RoleEnum

    model_config = {"from_attributes": True}
