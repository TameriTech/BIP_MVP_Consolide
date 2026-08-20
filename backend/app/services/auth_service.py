import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.account import Account
from app.models.enums import AccountStatus, RoleEnum
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenPair


def _issue_token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.role.value),
    )


def register_user(db: Session, data: RegisterRequest) -> tuple[User, TokenPair]:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing is not None:
        raise ConflictError("an account with this email already exists", {"field": "email"})

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role=RoleEnum.investor,
    )
    db.add(user)
    db.flush()

    account = Account(user_id=user.id, status=AccountStatus.pending)
    db.add(account)
    db.commit()
    db.refresh(user)

    return user, _issue_token_pair(user)


def authenticate_user(db: Session, email: str, password: str) -> tuple[User, TokenPair]:
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("invalid email or password")
    return user, _issue_token_pair(user)


def refresh_tokens(db: Session, refresh_token: str) -> TokenPair:
    try:
        payload = decode_token(refresh_token)
    except ValueError as exc:
        raise UnauthorizedError("invalid or expired refresh token") from exc
    if payload.get("type") != "refresh":
        raise UnauthorizedError("invalid token type")

    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise UnauthorizedError("user not found")
    return _issue_token_pair(user)


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("current password is incorrect")
    user.password_hash = hash_password(new_password)
    db.commit()


def _hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def request_password_reset(db: Session, email: str) -> str | None:
    """Issues a reset token for `email` if it matches an account, else no-ops.

    Returns the RAW token (or None). Never raises for an unknown email —
    the caller always returns the same generic message regardless, so this
    endpoint can't be used to enumerate registered emails via error/success
    branching. Only a hash of the token is ever persisted.
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None

    raw_token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_reset_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_expire_minutes),
        )
    )
    db.commit()
    return raw_token


def reset_password(db: Session, token: str, new_password: str) -> None:
    reset = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == _hash_reset_token(token))
        .first()
    )
    now = datetime.now(timezone.utc)
    if reset is None or reset.used_at is not None or reset.expires_at < now:
        raise UnauthorizedError("invalid or expired reset token")

    user = db.get(User, reset.user_id)
    user.password_hash = hash_password(new_password)
    reset.used_at = now
    db.commit()
