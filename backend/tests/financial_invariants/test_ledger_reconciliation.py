from decimal import Decimal

from app.models.enums import OrderSide, OrderStatus, OrderType
from app.models.execution import Execution
from app.models.ledger import LedgerEntry
from app.models.position import Position
from app.models.reservation import Reservation
from app.services import order_service
from tests.financial_invariants.conftest import make_funded_account, make_instrument


def test_ledger_sum_reconciles_with_cash_balance_across_multiple_trades(db):
    user, account = make_funded_account(db, "recon1@x.com", cash="5000.00")
    instrument = make_instrument(db, "RECON1", price="50.00")

    o1 = order_service.submit_order(db, account, instrument.id, OrderSide.buy, OrderType.market, Decimal("10"), None)
    o2 = order_service.submit_order(db, account, instrument.id, OrderSide.buy, OrderType.market, Decimal("5"), None)
    o3 = order_service.submit_order(db, account, instrument.id, OrderSide.sell, OrderType.market, Decimal("4"), None)
    assert [o1.status, o2.status, o3.status] == [OrderStatus.executed] * 3

    db.refresh(account)
    entries = db.query(LedgerEntry).filter(LedgerEntry.account_id == account.id).order_by(LedgerEntry.id).all()

    ledger_sum = sum((e.amount for e in entries), Decimal("0"))
    assert account.cash_balance == ledger_sum

    running = Decimal("0")
    for entry in entries:
        running += entry.amount
        assert entry.balance_after == running
    assert entries[-1].balance_after == account.cash_balance


def test_position_quantity_reconciles_with_executed_trades(db):
    user, account = make_funded_account(db, "recon2@x.com", cash="10000.00")
    instrument = make_instrument(db, "RECON2", price="20.00")

    order_service.submit_order(db, account, instrument.id, OrderSide.buy, OrderType.market, Decimal("100"), None)
    order_service.submit_order(db, account, instrument.id, OrderSide.buy, OrderType.market, Decimal("50"), None)
    order_service.submit_order(db, account, instrument.id, OrderSide.sell, OrderType.market, Decimal("30"), None)
    order_service.submit_order(db, account, instrument.id, OrderSide.sell, OrderType.market, Decimal("20"), None)

    position = (
        db.query(Position)
        .filter(Position.account_id == account.id, Position.instrument_id == instrument.id)
        .one()
    )
    assert position.quantity == Decimal("100")  # 100 + 50 - 30 - 20
    assert position.reserved_quantity == Decimal("0")


def test_full_chain_traceability_order_reservation_execution_ledger_position(db):
    user, account = make_funded_account(db, "trace1@x.com")
    instrument = make_instrument(db, "TRACE1")

    order = order_service.submit_order(db, account, instrument.id, OrderSide.buy, OrderType.market, Decimal("2"), None)
    assert order.status == OrderStatus.executed

    res = db.query(Reservation).filter(Reservation.order_id == order.id).one()
    assert res.status.value == "consumed"

    execution = db.query(Execution).filter(Execution.order_id == order.id).one()
    assert execution.instrument_id == instrument.id

    entries = db.query(LedgerEntry).filter(LedgerEntry.execution_id == execution.id).order_by(LedgerEntry.id).all()
    assert {e.entry_type.value for e in entries} == {"trade_buy", "fee"}
    assert all(e.order_id == order.id for e in entries)
    assert all(e.instrument_id == instrument.id for e in entries)

    position = (
        db.query(Position)
        .filter(Position.account_id == account.id, Position.instrument_id == instrument.id)
        .one()
    )
    assert position.quantity == Decimal("2")

    # navigable purely by foreign key, order -> reservation/execution -> ledger
    assert res.order_id == order.id
    assert execution.order_id == order.id
    assert res.account_id == order.account_id == account.id
