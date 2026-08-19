import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import AccountStatus, RoleEnum


class UserRoleUpdateRequest(BaseModel):
    role: RoleEnum


class AccountAdminOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: AccountStatus
    currency: str
    cash_balance: Decimal
    cash_reserved: Decimal
    activated_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AccountStatusUpdateRequest(BaseModel):
    status: AccountStatus


class AuditEventOut(BaseModel):
    id: int
    actor_user_id: uuid.UUID | None
    actor_role: str | None
    action: str
    entity_type: str
    entity_id: str | None
    event_metadata: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlatformSettingOut(BaseModel):
    key: str
    value: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlatformSettingUpdateRequest(BaseModel):
    value: dict
