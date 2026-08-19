"""Simulated execution — fills an already-reserved order and, in the SAME
transaction as the caller's, updates ledger + position + account cash
together. All-or-nothing: if anything here raises, the caller's transaction
rolls back everything (reservation included).
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.engine import fees, ledger_writer
from app.models.account import Account
from app.models.enums import LedgerEntryType, OrderSide, ReservationStatus
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.position import Position
from app.models.reservation import Reservation


def fill(
    db: Session,
    *,
    order: Order,
    account: Account,
    instrument: Instrument,
    position: Position,
    reservation: Reservation,
    exec_price: Decimal,
) -> Execution:
    gross = (order.quantity * exec_price).quantize(Decimal("0.01"))
    fee = fees.compute(gross)
    net = gross + fee if order.side == OrderSide.buy else gross - fee

    execution = Execution(
        order_id=order.id, instrument_id=instrument.id, quantity=order.quantity, price=exec_price,
        fees=fee, gross_amount=gross, net_amount=net,
    )
    db.add(execution)
    db.flush()

    if order.side == OrderSide.buy:
        # Release the FULL originally-reserved hold, but debit only the actual
        # gross+fee — keeps cash_reserved/cash_balance exact even if exec_price
        # differs from the price the reservation was sized against (limit orders
        # can legitimately fill better than their limit).
        account.cash_reserved -= reservation.amount
        total_qty = position.quantity + order.quantity
        position.avg_cost = (
            ((position.quantity * position.avg_cost) + gross) / total_qty if total_qty > 0 else Decimal("0")
        )
        position.quantity = total_qty
        # Apply the cash debit and write its ledger entry one at a time — NOT
        # combined — so `balance_after` on each entry is a true running
        # snapshot at the moment that entry landed, not a preview of a later one.
        account.cash_balance -= gross
        ledger_writer.append(
            db, account=account, entry_type=LedgerEntryType.trade_buy, amount=-gross,
            order_id=order.id, execution_id=execution.id, instrument_id=instrument.id,
        )
    else:
        position.reserved_quantity -= order.quantity
        position.quantity -= order.quantity
        account.cash_balance += gross
        ledger_writer.append(
            db, account=account, entry_type=LedgerEntryType.trade_sell, amount=gross,
            order_id=order.id, execution_id=execution.id, instrument_id=instrument.id,
        )

    account.cash_balance -= fee
    ledger_writer.append(
        db, account=account, entry_type=LedgerEntryType.fee, amount=-fee,
        order_id=order.id, execution_id=execution.id, instrument_id=instrument.id,
    )

    reservation.status = ReservationStatus.consumed
    return execution
