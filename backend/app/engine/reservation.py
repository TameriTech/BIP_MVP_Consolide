"""Resource reservation (doc §17) — the mechanism that stops the same cash or
the same shares from being used by two concurrent orders.

Callers are responsible for holding a `SELECT ... FOR UPDATE` lock on the
`Account` row (and, for sells, the `Position` row) for the full duration of
the check-then-reserve sequence — that lock is what actually serializes
concurrent orders on the same account; this module just does the arithmetic
and bookkeeping once the lock is held. Fixed lock order everywhere: account,
then position, to avoid deadlocks.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import OrderSide, ReservationKind, ReservationStatus
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.position import Position
from app.models.reservation import Reservation


def get_or_create_locked_position(db: Session, account_id, instrument_id) -> Position:
    # populate_existing=True: same reasoning as app/engine/locking.py — a
    # Position for this (account, instrument) pair may already be identity-mapped
    # from an earlier unlocked read in this session, and without this the lock
    # would be acquired correctly but the in-memory quantity/reserved_quantity
    # returned to the caller could still be a stale pre-lock snapshot.
    position = db.execute(
        select(Position)
        .where(Position.account_id == account_id, Position.instrument_id == instrument_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if position is None:
        position = Position(account_id=account_id, instrument_id=instrument_id)
        db.add(position)
        db.flush()
    return position


def reserve(db: Session, account: Account, instrument: Instrument, order: Order, position: Position | None) -> str | None:
    """Reserves what `order` needs on the already-locked `account`/`position`.

    Returns None on success (Reservation row created, account/position hold
    updated), or a rejection reason string if there isn't enough available —
    in which case nothing is reserved.
    """
    if order.side == OrderSide.buy:
        needed: Decimal = order.estimated_amount + order.estimated_fees
        available = account.cash_balance - account.cash_reserved
        if available < needed:
            return f"insufficient funds: need {needed}, have {available} available"
        account.cash_reserved += needed
        reservation = Reservation(
            order_id=order.id, account_id=account.id, kind=ReservationKind.cash,
            amount=needed, status=ReservationStatus.active,
        )
    else:
        assert position is not None
        available_qty = position.quantity - position.reserved_quantity
        if available_qty < order.quantity:
            return f"insufficient shares: need {order.quantity}, have {available_qty} available"
        position.reserved_quantity += order.quantity
        reservation = Reservation(
            order_id=order.id, account_id=account.id, kind=ReservationKind.shares,
            instrument_id=instrument.id, quantity=order.quantity, status=ReservationStatus.active,
        )

    db.add(reservation)
    db.flush()
    return None


def release(db: Session, reservation: Reservation, account: Account, position: Position | None) -> None:
    """Fully releases an active hold (order cancelled, or rejected at execution time)."""
    if reservation.status != ReservationStatus.active:
        return
    if reservation.kind == ReservationKind.cash:
        account.cash_reserved -= reservation.amount
    else:
        assert position is not None
        position.reserved_quantity -= reservation.quantity
    reservation.status = ReservationStatus.released
    reservation.released_at = datetime.now(timezone.utc)
