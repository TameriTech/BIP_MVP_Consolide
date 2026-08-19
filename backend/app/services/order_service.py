import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.engine import execution_engine, fees, oms, pretrade_checks, reservation
from app.engine.locking import lock_row
from app.models.account import Account
from app.models.enums import OrderSide, OrderStatus, OrderType
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.reservation import Reservation
from app.services import audit_service


def submit_order(
    db: Session,
    account: Account,
    instrument_id: uuid.UUID,
    side: OrderSide,
    order_type: OrderType,
    quantity: Decimal,
    limit_price: Decimal | None,
) -> Order:
    """The whole order lifecycle — pretrade checks, reservation, and (since the
    MVP has no execution queue) immediate simulated fill — as ONE atomic DB
    transaction. Combining reserve+execute into a single transaction (rather
    than two, as a queued design would) means the exact same `instrument.last_price`
    read is used for both reservation sizing and the fill itself, which is what
    guarantees a market order can never execute for more than what was reserved.
    Any failure below rolls back the whole thing — an order is only ever left
    in a terminal state (rejected/executed), never stranded mid-flight.

    Note: this does NOT wrap the body in `with db.begin():` — SQLAlchemy 2.0
    sessions auto-begin a transaction on first use, and by the time this runs,
    the `get_current_user` auth dependency has already touched `db`, so an
    explicit `db.begin()` here would raise ("a transaction is already begun on
    this Session"). Every exit path below calls `db.commit()` explicitly
    instead, with a catch-all rollback on any unexpected exception.
    """
    try:
        locked_account = lock_row(db, Account, account.id)

        instrument = db.get(Instrument, instrument_id)
        if instrument is None:
            raise NotFoundError("instrument not found")

        reason = pretrade_checks.evaluate(db, locked_account, instrument, order_type, limit_price)

        ref_price = limit_price if order_type == OrderType.limit else instrument.last_price
        gross = (quantity * ref_price).quantize(Decimal("0.01")) if ref_price is not None else None
        fee = fees.compute(gross) if gross is not None else None

        order = Order(
            account_id=locked_account.id, instrument_id=instrument.id, side=side, order_type=order_type,
            quantity=quantity, limit_price=limit_price, estimated_amount=gross, estimated_fees=fee,
            status=OrderStatus.submitted, submitted_at=datetime.now(timezone.utc),
        )
        db.add(order)
        db.flush()

        if reason is not None:
            order.rejection_reason = reason
            oms.transition(order, OrderStatus.rejected)
            audit_service.log(
                db, actor_user_id=locked_account.user_id, actor_role="investor", action="order.rejected",
                entity_type="order", entity_id=order.id, metadata={"reason": reason},
            )
            db.commit()
            return order

        position = (
            reservation.get_or_create_locked_position(db, locked_account.id, instrument.id)
            if side == OrderSide.sell
            else None
        )
        rejection = reservation.reserve(db, locked_account, instrument, order, position)
        if rejection is not None:
            order.rejection_reason = rejection
            oms.transition(order, OrderStatus.rejected)
            audit_service.log(
                db, actor_user_id=locked_account.user_id, actor_role="investor", action="order.rejected",
                entity_type="order", entity_id=order.id, metadata={"reason": rejection},
            )
            db.commit()
            return order

        oms.transition(order, OrderStatus.reserved)
        res = db.query(Reservation).filter(Reservation.order_id == order.id).one()
        if position is None:
            position = reservation.get_or_create_locked_position(db, locked_account.id, instrument.id)

        if order_type == OrderType.limit:
            exec_price = instrument.last_price if instrument.last_price is not None else limit_price
            satisfiable = (
                exec_price <= limit_price if side == OrderSide.buy else exec_price >= limit_price
            )
            if not satisfiable:
                reservation.release(db, res, locked_account, position)
                reason = f"limit price {limit_price} not satisfiable at reference price {exec_price}"
                order.rejection_reason = reason
                oms.transition(order, OrderStatus.rejected)
                audit_service.log(
                    db, actor_user_id=locked_account.user_id, actor_role="investor", action="order.rejected",
                    entity_type="order", entity_id=order.id, metadata={"reason": reason},
                )
                db.commit()
                return order
        else:
            exec_price = ref_price  # same price the reservation was sized against — no race possible

        execution_engine.fill(
            db, order=order, account=locked_account, instrument=instrument, position=position,
            reservation=res, exec_price=exec_price,
        )
        oms.transition(order, OrderStatus.executed)
        audit_service.log(
            db, actor_user_id=locked_account.user_id, actor_role="investor", action="order.executed",
            entity_type="order", entity_id=order.id,
            metadata={"side": side.value, "quantity": str(quantity), "exec_price": str(exec_price)},
        )
        db.commit()
        return order
    except Exception:
        db.rollback()
        raise


def cancel_order(db: Session, order: Order) -> Order:
    try:
        locked_order = lock_row(db, Order, order.id)
        if locked_order.status != OrderStatus.reserved:
            raise ConflictError(
                "only a reserved order can be cancelled", {"status": locked_order.status.value}
            )
        account = lock_row(db, Account, locked_order.account_id)
        res = db.query(Reservation).filter(Reservation.order_id == locked_order.id).one()
        position = None
        if res.kind.value == "shares":
            position = reservation.get_or_create_locked_position(db, account.id, locked_order.instrument_id)
        reservation.release(db, res, account, position)
        oms.transition(locked_order, OrderStatus.cancelled)
        audit_service.log(
            db, actor_user_id=account.user_id, actor_role="investor", action="order.cancelled",
            entity_type="order", entity_id=locked_order.id,
        )
        db.commit()
        return locked_order
    except Exception:
        db.rollback()
        raise


def get_order(db: Session, order_id: uuid.UUID, account_id: uuid.UUID | None = None) -> Order:
    query = db.query(Order).filter(Order.id == order_id)
    if account_id is not None:
        query = query.filter(Order.account_id == account_id)
    order = query.first()
    if order is None:
        raise NotFoundError("order not found")
    return order


def list_orders(
    db: Session, account_id: uuid.UUID | None = None, status: OrderStatus | None = None,
    instrument_id: uuid.UUID | None = None,
) -> list[Order]:
    query = db.query(Order)
    if account_id is not None:
        query = query.filter(Order.account_id == account_id)
    if status is not None:
        query = query.filter(Order.status == status)
    if instrument_id is not None:
        query = query.filter(Order.instrument_id == instrument_id)
    return query.order_by(Order.created_at.desc()).all()


def list_executions_for_order(db: Session, order_id: uuid.UUID) -> list[Execution]:
    return db.query(Execution).filter(Execution.order_id == order_id).order_by(Execution.executed_at).all()
