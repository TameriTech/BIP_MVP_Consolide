import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.enums import RoleEnum
from app.models.user import User

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession, authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise UnauthorizedError("invalid or expired token") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("invalid token type")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise UnauthorizedError("user not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: RoleEnum):
    def _check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"requires one of roles: {[r.value for r in roles]}")
        return user

    return _check
