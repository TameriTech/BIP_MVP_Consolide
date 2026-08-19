import uuid

from sqlalchemy.orm import Session

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
