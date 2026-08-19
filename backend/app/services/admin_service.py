import uuid

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.account import Account
from app.models.audit import AuditEvent
from app.models.enums import AccountStatus, RoleEnum
from app.models.execution import Execution
from app.models.order import Order
from app.models.settings import PlatformSetting
from app.models.user import User
from app.services import audit_service


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("user not found")
    return user


def update_user_role(db: Session, user: User, new_role: RoleEnum, actor: User) -> User:
    old_role = user.role
    user.role = new_role
    audit_service.log(
        db, actor_user_id=actor.id, actor_role=actor.role.value, action="user.role_change",
        entity_type="user", entity_id=user.id, metadata={"from": old_role.value, "to": new_role.value},
    )
    db.commit()
    db.refresh(user)
    return user


def list_accounts(db: Session, status: AccountStatus | None = None) -> list[Account]:
    query = db.query(Account)
    if status is not None:
        query = query.filter(Account.status == status)
    return query.order_by(Account.created_at.desc()).all()


def get_account(db: Session, account_id: uuid.UUID) -> Account:
    account = db.get(Account, account_id)
    if account is None:
        raise NotFoundError("account not found")
    return account


def update_account_status(db: Session, account: Account, new_status: AccountStatus, actor: User) -> Account:
    old_status = account.status
    account.status = new_status
    audit_service.log(
        db, actor_user_id=actor.id, actor_role=actor.role.value, action="account.status_change",
        entity_type="account", entity_id=account.id, metadata={"from": old_status.value, "to": new_status.value},
    )
    db.commit()
    db.refresh(account)
    return account


def list_all_orders(
    db: Session, status=None, account_id: uuid.UUID | None = None
) -> list[Order]:
    query = db.query(Order)
    if status is not None:
        query = query.filter(Order.status == status)
    if account_id is not None:
        query = query.filter(Order.account_id == account_id)
    return query.order_by(Order.created_at.desc()).all()


def list_all_executions(db: Session) -> list[Execution]:
    return db.query(Execution).order_by(Execution.executed_at.desc()).all()


def list_audit_events(
    db: Session, actor_user_id: uuid.UUID | None = None, entity_type: str | None = None, action: str | None = None
) -> list[AuditEvent]:
    query = db.query(AuditEvent)
    if actor_user_id is not None:
        query = query.filter(AuditEvent.actor_user_id == actor_user_id)
    if entity_type is not None:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if action is not None:
        query = query.filter(AuditEvent.action == action)
    return query.order_by(AuditEvent.created_at.desc()).all()


def get_settings(db: Session) -> list[PlatformSetting]:
    return db.query(PlatformSetting).order_by(PlatformSetting.key).all()


def update_setting(db: Session, key: str, value: dict, actor: User) -> PlatformSetting:
    setting = db.get(PlatformSetting, key)
    if setting is None:
        setting = PlatformSetting(key=key, value=value, updated_by=actor.id)
        db.add(setting)
    else:
        setting.value = value
        setting.updated_by = actor.id
    audit_service.log(
        db, actor_user_id=actor.id, actor_role=actor.role.value, action="settings.update",
        entity_type="platform_setting", entity_id=key, metadata={"value": value},
    )
    db.commit()
    db.refresh(setting)
    return setting
