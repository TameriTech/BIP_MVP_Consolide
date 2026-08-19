import uuid

import pytest

from app.core.deps import require_role
from app.core.errors import ForbiddenError
from app.models.enums import RoleEnum
from app.models.user import User


def _user(role: RoleEnum) -> User:
    return User(id=uuid.uuid4(), email="x@example.com", password_hash="h", full_name="X", role=role)


def test_require_role_allows_matching_role():
    check = require_role(RoleEnum.admin, RoleEnum.super_admin)
    user = _user(RoleEnum.admin)
    assert check(user) is user


def test_require_role_rejects_non_matching_role():
    check = require_role(RoleEnum.admin, RoleEnum.super_admin)
    user = _user(RoleEnum.investor)
    with pytest.raises(ForbiddenError):
        check(user)
