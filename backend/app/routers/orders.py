import uuid

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.models.enums import OrderStatus
from app.schemas.order import ExecutionOut, OrderCreateRequest, OrderOut
from app.services import account_service, order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
def submit_order(data: OrderCreateRequest, db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    return order_service.submit_order(
        db, account, data.instrument_id, data.side, data.order_type, data.quantity, data.limit_price
    )


@router.get("", response_model=list[OrderOut])
def list_my_orders(
    db: DbSession, user: CurrentUser, status_filter: OrderStatus | None = None,
    instrument_id: uuid.UUID | None = None,
):
    account = account_service.get_account_for_user(db, user)
    return order_service.list_orders(db, account.id, status_filter, instrument_id)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: uuid.UUID, db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    return order_service.get_order(db, order_id, account.id)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: uuid.UUID, db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    order = order_service.get_order(db, order_id, account.id)
    return order_service.cancel_order(db, order)


@router.get("/{order_id}/executions", response_model=list[ExecutionOut])
def list_order_executions(order_id: uuid.UUID, db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    order_service.get_order(db, order_id, account.id)  # 404s / scopes to caller's own order
    return order_service.list_executions_for_order(db, order_id)
