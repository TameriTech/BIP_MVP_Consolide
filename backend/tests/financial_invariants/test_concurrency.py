"""The single most important test in the suite: direct proof that the
`SELECT ... FOR UPDATE` row-locking design in app/engine/reservation.py
actually serializes concurrent orders against the same account/position, so
the same cash — or the same shares — can never be spent/sold twice.

This needs REAL concurrent DB transactions on separate connections, which the
rollback-wrapped `db` fixture (a single connection + SAVEPOINT) cannot provide
— two "concurrent" calls on one connection aren't concurrent at all. So this
file talks to the shared test engine directly, with each thread owning its
own Session/connection, and cleans up the committed rows it creates.
"""

import threading
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.engine import ledger_writer
from app.models.account import Account
from app.models.enums import AccountStatus, KycStatus, LedgerEntryType, OrderSide, OrderStatus, OrderType, RoleEnum
from app.models.instrument import Instrument
from app.models.kyc import KycFile
from app.models.ledger import LedgerEntry
from app.models.position import Position
from app.models.user import User
from app.services import order_service
from tests.conftest import engine as test_engine

SessionFactory = sessionmaker(bind=test_engine)


def _run_concurrently(fns: list) -> list:
    results = [None] * len(fns)
    threads = []

    def _wrap(i, fn):
        results[i] = fn()

    for i, fn in enumerate(fns):
        t = threading.Thread(target=_wrap, args=(i, fn))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def test_concurrent_buy_orders_never_double_spend_cash():
    setup = SessionFactory()
    try:
        user = User(email="conc_cash@x.com", password_hash=hash_password("x"), full_name="C", role=RoleEnum.investor)
        setup.add(user)
        setup.flush()
        account = Account(
            user_id=user.id, status=AccountStatus.active, cash_balance=Decimal("0"),
            activated_at=datetime.now(timezone.utc),
        )
        setup.add(account)
        setup.flush()
        setup.add(KycFile(account_id=account.id, status=KycStatus.validated, full_legal_name="C",
                           id_document_number="X", reviewed_at=datetime.now(timezone.utc)))
        account.cash_balance = Decimal("1000.00")
        ledger_writer.append(setup, account=account, entry_type=LedgerEntryType.initial_credit, amount=Decimal("1000.00"))
        instrument = Instrument(symbol="CONCCASH", name="Concurrent Cash Co", market="DEMO", currency="USD",
                                 tradable=True, last_price=Decimal("100.00"), last_price_at=datetime.now(timezone.utc))
        setup.add(instrument)
        setup.commit()
        account_id, instrument_id, user_id = account.id, instrument.id, user.id
    finally:
        setup.close()

    # Each thread buys 3 shares @ $100 = $300 gross + $0.30 fee (10bps) = $300.30.
    # $1000.00 available covers exactly 3 (3*300.30=900.90) but not 4 (1201.20>1000).
    N_THREADS = 6

    def attempt():
        session = SessionFactory()
        try:
            account = session.get(Account, account_id)
            order = order_service.submit_order(
                session, account, instrument_id, OrderSide.buy, OrderType.market, Decimal("3"), None,
            )
            return order.status
        finally:
            session.close()

    try:
        results = _run_concurrently([attempt] * N_THREADS)

        executed = [r for r in results if r == OrderStatus.executed]
        rejected = [r for r in results if r == OrderStatus.rejected]
        assert len(executed) == 3, f"expected exactly 3 affordable fills, got statuses: {results}"
        assert len(rejected) == N_THREADS - 3

        verify = SessionFactory()
        try:
            account = verify.get(Account, account_id)
            assert account.cash_reserved == Decimal("0.00")
            assert account.cash_balance == Decimal("1000.00") - Decimal("900.90")

            entries = verify.query(LedgerEntry).filter(LedgerEntry.account_id == account_id).all()
            assert len(entries) == 7  # 1 initial_credit + 3 executed orders * (trade_buy + fee)
            assert sum((e.amount for e in entries), Decimal("0")) == account.cash_balance

            position = (
                verify.query(Position)
                .filter(Position.account_id == account_id, Position.instrument_id == instrument_id)
                .one()
            )
            assert position.quantity == Decimal("9")  # 3 executed * 3 shares
            assert position.reserved_quantity == Decimal("0")
        finally:
            verify.close()
    finally:
        _cleanup(account_id, instrument_id, user_id)


def test_concurrent_sell_orders_never_double_sell_shares():
    setup = SessionFactory()
    try:
        user = User(email="conc_shares@x.com", password_hash=hash_password("x"), full_name="C", role=RoleEnum.investor)
        setup.add(user)
        setup.flush()
        account = Account(
            user_id=user.id, status=AccountStatus.active, cash_balance=Decimal("100000.00"),
            activated_at=datetime.now(timezone.utc),
        )
        setup.add(account)
        setup.flush()
        setup.add(KycFile(account_id=account.id, status=KycStatus.validated, full_legal_name="C",
                           id_document_number="X", reviewed_at=datetime.now(timezone.utc)))
        instrument = Instrument(symbol="CONCSHR", name="Concurrent Shares Co", market="DEMO", currency="USD",
                                 tradable=True, last_price=Decimal("10.00"), last_price_at=datetime.now(timezone.utc))
        setup.add(instrument)
        setup.flush()
        # Holds exactly 25 shares — enough for 5 sell-5 orders, not 6.
        position = Position(account_id=account.id, instrument_id=instrument.id, quantity=Decimal("25"), avg_cost=Decimal("5"))
        setup.add(position)
        setup.commit()
        account_id, instrument_id, user_id = account.id, instrument.id, user.id
    finally:
        setup.close()

    N_THREADS = 8

    def attempt():
        session = SessionFactory()
        try:
            account = session.get(Account, account_id)
            order = order_service.submit_order(
                session, account, instrument_id, OrderSide.sell, OrderType.market, Decimal("5"), None,
            )
            return order.status
        finally:
            session.close()

    try:
        results = _run_concurrently([attempt] * N_THREADS)

        executed = [r for r in results if r == OrderStatus.executed]
        rejected = [r for r in results if r == OrderStatus.rejected]
        assert len(executed) == 5, f"expected exactly 5 affordable sells, got statuses: {results}"
        assert len(rejected) == N_THREADS - 5

        verify = SessionFactory()
        try:
            position = (
                verify.query(Position)
                .filter(Position.account_id == account_id, Position.instrument_id == instrument_id)
                .one()
            )
            assert position.quantity == Decimal("0")  # 25 - 5*5
            assert position.reserved_quantity == Decimal("0")
        finally:
            verify.close()
    finally:
        _cleanup(account_id, instrument_id, user_id)


def _cleanup(account_id, instrument_id, user_id) -> None:
    """These rows were committed (required for cross-connection visibility, the
    whole point of this test) so — unlike every other test here — they are NOT
    auto-rolled-back by the shared `db` fixture. Remove them explicitly.
    """
    from app.models.execution import Execution
    from app.models.kyc import KycFile
    from app.models.order import Order
    from app.models.reservation import Reservation

    from app.models.audit import AuditEvent

    session = SessionFactory()
    try:
        order_ids = [o.id for o in session.query(Order.id).filter(Order.account_id == account_id)]
        # ledger_entries/audit_events reference executions/orders/users, so they must go first.
        session.query(LedgerEntry).filter(LedgerEntry.account_id == account_id).delete(synchronize_session=False)
        session.query(AuditEvent).filter(AuditEvent.actor_user_id == user_id).delete(synchronize_session=False)
        if order_ids:
            session.query(Execution).filter(Execution.order_id.in_(order_ids)).delete(synchronize_session=False)
            session.query(Reservation).filter(Reservation.order_id.in_(order_ids)).delete(synchronize_session=False)
            session.query(Order).filter(Order.id.in_(order_ids)).delete(synchronize_session=False)
        session.query(Position).filter(Position.account_id == account_id).delete(synchronize_session=False)
        session.query(KycFile).filter(KycFile.account_id == account_id).delete(synchronize_session=False)
        session.query(Account).filter(Account.id == account_id).delete(synchronize_session=False)
        session.query(Instrument).filter(Instrument.id == instrument_id).delete(synchronize_session=False)
        session.query(User).filter(User.id == user_id).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()
