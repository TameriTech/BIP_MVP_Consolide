import uuid
from datetime import datetime

from fastapi import APIRouter, Depends

from app.core.deps import DbSession, require_role
from app.models.enums import AccountStatus, KycStatus, LedgerEntryType, OrderStatus, RoleEnum
from app.models.user import User
from app.schemas.admin import (
    AccountAdminOut, AccountStatusUpdateRequest, AuditEventOut,
    PlatformSettingOut, PlatformSettingUpdateRequest, UserRoleUpdateRequest,
)
from app.schemas.auth import UserOut
from app.schemas.kyc import KycOut, KycRejectRequest
from app.schemas.ledger import LedgerEntryOut
from app.schemas.market import InstrumentCreateRequest, InstrumentOut, InstrumentUpdateRequest
from app.schemas.order import ExecutionOut, OrderOut
from app.services import admin_service, kyc_service, ledger_service, market_data_service, market_service

router = APIRouter(prefix="/backoffice", tags=["backoffice"])

_reviewer_roles = (RoleEnum.admin, RoleEnum.backoffice_operator, RoleEnum.super_admin)
_super_admin_only = (RoleEnum.super_admin,)


@router.get("/kyc", response_model=list[KycOut], dependencies=[Depends(require_role(*_reviewer_roles))])
def list_kyc(db: DbSession, status_filter: KycStatus | None = None):
    return kyc_service.list_kyc(db, status_filter)


@router.get("/kyc/{kyc_id}", response_model=KycOut, dependencies=[Depends(require_role(*_reviewer_roles))])
def get_kyc(kyc_id: uuid.UUID, db: DbSession):
    return kyc_service.get_kyc_by_id(db, kyc_id)


@router.post("/kyc/{kyc_id}/validate", response_model=KycOut)
def validate_kyc(kyc_id: uuid.UUID, db: DbSession, reviewer=Depends(require_role(*_reviewer_roles))):
    kyc = kyc_service.get_kyc_by_id(db, kyc_id)
    return kyc_service.validate_kyc(db, kyc, reviewer)


@router.post("/kyc/{kyc_id}/reject", response_model=KycOut)
def reject_kyc(
    kyc_id: uuid.UUID, data: KycRejectRequest, db: DbSession, reviewer=Depends(require_role(*_reviewer_roles))
):
    kyc = kyc_service.get_kyc_by_id(db, kyc_id)
    return kyc_service.reject_kyc(db, kyc, reviewer, data.reason)


@router.post(
    "/instruments",
    response_model=InstrumentOut,
    status_code=201,
    dependencies=[Depends(require_role(*_reviewer_roles))],
)
def create_instrument(data: InstrumentCreateRequest, db: DbSession):
    return market_service.create_instrument(db, data.model_dump())


@router.patch(
    "/instruments/{instrument_id}",
    response_model=InstrumentOut,
    dependencies=[Depends(require_role(*_reviewer_roles))],
)
def update_instrument(instrument_id: uuid.UUID, data: InstrumentUpdateRequest, db: DbSession):
    instrument = market_service.get_instrument_by_id(db, instrument_id)
    return market_service.update_instrument(db, instrument, data.model_dump(exclude_unset=True))


@router.post("/market/refresh", dependencies=[Depends(require_role(*_reviewer_roles))])
def refresh_market(db: DbSession):
    return market_data_service.refresh_latest(db)


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_role(*_reviewer_roles))])
def list_users(db: DbSession):
    return admin_service.list_users(db)


@router.get("/users/{user_id}", response_model=UserOut, dependencies=[Depends(require_role(*_reviewer_roles))])
def get_user(user_id: uuid.UUID, db: DbSession):
    return admin_service.get_user(db, user_id)


@router.patch("/users/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: uuid.UUID, data: UserRoleUpdateRequest, db: DbSession,
    actor: User = Depends(require_role(*_super_admin_only)),
):
    user = admin_service.get_user(db, user_id)
    return admin_service.update_user_role(db, user, data.role, actor)


@router.get("/accounts", response_model=list[AccountAdminOut], dependencies=[Depends(require_role(*_reviewer_roles))])
def list_accounts(db: DbSession, status_filter: AccountStatus | None = None):
    return admin_service.list_accounts(db, status_filter)


@router.patch("/accounts/{account_id}/status", response_model=AccountAdminOut)
def update_account_status(
    account_id: uuid.UUID, data: AccountStatusUpdateRequest, db: DbSession,
    actor: User = Depends(require_role(*_reviewer_roles)),
):
    account = admin_service.get_account(db, account_id)
    return admin_service.update_account_status(db, account, data.status, actor)


@router.get("/orders", response_model=list[OrderOut], dependencies=[Depends(require_role(*_reviewer_roles))])
def list_all_orders(
    db: DbSession, status_filter: OrderStatus | None = None, account_id: uuid.UUID | None = None
):
    return admin_service.list_all_orders(db, status_filter, account_id)


@router.get("/executions", response_model=list[ExecutionOut], dependencies=[Depends(require_role(*_reviewer_roles))])
def list_all_executions(db: DbSession):
    return admin_service.list_all_executions(db)


@router.get("/ledger", response_model=list[LedgerEntryOut], dependencies=[Depends(require_role(*_reviewer_roles))])
def list_all_ledger_entries(
    db: DbSession, account_id: uuid.UUID | None = None, date_from: datetime | None = None,
    date_to: datetime | None = None, entry_type: LedgerEntryType | None = None,
):
    return ledger_service.list_ledger_entries(db, account_id, date_from, date_to, entry_type)


@router.get("/audit-log", response_model=list[AuditEventOut], dependencies=[Depends(require_role(*_reviewer_roles))])
def list_audit_log(
    db: DbSession, actor_user_id: uuid.UUID | None = None, entity_type: str | None = None, action: str | None = None
):
    return admin_service.list_audit_events(db, actor_user_id, entity_type, action)


@router.get("/settings", response_model=list[PlatformSettingOut], dependencies=[Depends(require_role(*_reviewer_roles))])
def get_settings(db: DbSession):
    return admin_service.get_settings(db)


@router.patch("/settings/{key}", response_model=PlatformSettingOut)
def update_setting(
    key: str, data: PlatformSettingUpdateRequest, db: DbSession,
    actor: User = Depends(require_role(*_super_admin_only)),
):
    return admin_service.update_setting(db, key, data.value, actor)
