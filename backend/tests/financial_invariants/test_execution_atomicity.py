from decimal import Decimal

import pytest

from app.engine import ledger_writer
from app.models.enums import OrderSide, OrderType
from app.models.ledger import LedgerEntry
from app.models.position import Position
from app.services import order_service
from tests.financial_invariants.conftest import make_funded_account, make_instrument


def test_a_failure_partway_through_execution_rolls_back_everything(db, monkeypatch):
    """execution_engine.fill() writes two ledger entries (trade_buy, then fee)
    plus position/account updates in one transaction. If the SECOND ledger
    write blows up, nothing from this order attempt — not the first ledger
    entry, not the cash debit, not the position update, not the reservation —
    may survive. This is the direct proof of "all-or-nothing" execution.
    """
    user, account = make_funded_account(db, "atomicity1@x.com", cash="5000.00")
    instrument = make_instrument(db, "ATOM1", price="100.00")

    balance_before = account.cash_balance
    ledger_count_before = db.query(LedgerEntry).filter(LedgerEntry.account_id == account.id).count()

    calls = {"n": 0}
    original_append = ledger_writer.append

    def flaky_append(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:  # let the trade_buy entry through, blow up on the fee entry
            raise RuntimeError("simulated mid-execution failure")
        return original_append(*args, **kwargs)

    monkeypatch.setattr(ledger_writer, "append", flaky_append)

    with pytest.raises(RuntimeError):
        order_service.submit_order(db, account, instrument.id, OrderSide.buy, OrderType.market, Decimal("5"), None)

    db.refresh(account)
    assert account.cash_balance == balance_before
    assert account.cash_reserved == Decimal("0.00")

    ledger_count_after = db.query(LedgerEntry).filter(LedgerEntry.account_id == account.id).count()
    assert ledger_count_after == ledger_count_before  # the surviving trade_buy write was rolled back too

    position = (
        db.query(Position)
        .filter(Position.account_id == account.id, Position.instrument_id == instrument.id)
        .first()
    )
    assert position is None or position.quantity == Decimal("0")


def test_ledger_writer_exposes_only_append():
    """Static contract check: the ledger is append-only by construction — no
    update/delete function exists anywhere in the writer module for anyone to
    call, so a correction can only ever be a new, offsetting entry.
    """
    import app.engine.ledger_writer as lw

    public_callables = [
        name
        for name in dir(lw)
        if not name.startswith("_")
        and callable(getattr(lw, name))
        and getattr(getattr(lw, name), "__module__", None) == lw.__name__
    ]
    assert public_callables == ["append"]
