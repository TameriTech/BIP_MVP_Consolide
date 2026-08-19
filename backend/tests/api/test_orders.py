from datetime import datetime, timezone
from decimal import Decimal

from app.core.security import hash_password
from app.models.account import Account
from app.models.enums import (
    AccountStatus, KycStatus, LedgerEntryType, OrderSide, OrderStatus, OrderType,
    ReservationKind, ReservationStatus, RoleEnum,
)
from app.models.instrument import Instrument
from app.models.kyc import KycFile
from app.models.ledger import LedgerEntry
from app.models.order import Order
from app.models.position import Position
from app.models.reservation import Reservation
from app.models.user import User


def _funded_investor(db, email="trader@x.com", cash="10000.00"):
    user = User(email=email, password_hash=hash_password("StrongPass123!"), full_name="Trader", role=RoleEnum.investor)
    db.add(user)
    db.flush()
    account = Account(
        user_id=user.id, status=AccountStatus.active, cash_balance=Decimal(cash),
        activated_at=datetime.now(timezone.utc),
    )
    db.add(account)
    db.flush()
    db.add(KycFile(account_id=account.id, status=KycStatus.validated, full_legal_name="Trader",
                    id_document_number="P1", reviewed_at=datetime.now(timezone.utc)))
    db.add(LedgerEntry(reference="seed-credit-" + email, account_id=account.id,
                        entry_type=LedgerEntryType.initial_credit,
                        amount=Decimal(cash), currency="USD", balance_after=Decimal(cash)))
    db.commit()
    db.refresh(account)
    return user, account


def _login(client, email, password="StrongPass123!"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def _instrument(db, symbol="AAPL", price="100.00", tradable=True):
    instrument = Instrument(symbol=symbol, name=symbol, market="DEMO", currency="USD", tradable=tradable,
                             last_price=Decimal(price), last_price_at=datetime.now(timezone.utc))
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


def test_market_buy_order_executes_and_updates_everything(client, db):
    user, account = _funded_investor(db, "buyer1@x.com")
    instrument = _instrument(db, "AAPL", "100.00")
    token = _login(client, "buyer1@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "10"},
    )
    assert r.status_code == 201
    order = r.json()
    assert order["status"] == "executed"
    assert order["rejection_reason"] is None

    db.refresh(account)
    # 10 * 100 = 1000 gross, fee = 1000 * 10bps = 1.00 -> total debit 1001.00
    assert account.cash_balance == Decimal("8999.00")
    assert account.cash_reserved == Decimal("0.00")

    position = db.query(Position).filter(Position.account_id == account.id, Position.instrument_id == instrument.id).first()
    assert position.quantity == Decimal("10")
    assert position.reserved_quantity == Decimal("0")
    assert position.avg_cost == Decimal("100.000000")

    entries = db.query(LedgerEntry).filter(LedgerEntry.account_id == account.id).order_by(LedgerEntry.id).all()
    # seed credit + trade_buy + fee = 3 entries
    assert len(entries) == 3
    assert entries[-2].entry_type.value == "trade_buy"
    assert entries[-2].amount == Decimal("-1000.00")
    assert entries[-1].entry_type.value == "fee"
    assert entries[-1].amount == Decimal("-1.00")
    assert entries[-1].balance_after == account.cash_balance

    r = client.get(f"/api/v1/orders/{order['id']}/executions", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["gross_amount"] == "1000.00"


def test_sell_order_executes_and_releases_position(client, db):
    user, account = _funded_investor(db, "seller1@x.com")
    instrument = _instrument(db, "MSFT", "50.00")
    # give the account an existing position to sell from
    position = Position(account_id=account.id, instrument_id=instrument.id, quantity=Decimal("20"), avg_cost=Decimal("40"))
    db.add(position)
    db.commit()

    token = _login(client, "seller1@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "sell", "order_type": "market", "quantity": "5"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "executed"

    db.refresh(position)
    assert position.quantity == Decimal("15")
    assert position.reserved_quantity == Decimal("0")

    db.refresh(account)
    # 5*50=250 gross, fee=0.25, net credit = 249.75
    assert account.cash_balance == Decimal("10000.00") + Decimal("249.75")


def test_buy_order_rejected_for_insufficient_funds(client, db):
    user, account = _funded_investor(db, "poor1@x.com", cash="50.00")
    instrument = _instrument(db, "TSLA", "100.00")
    token = _login(client, "poor1@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "1"},
    )
    assert r.status_code == 201
    order = r.json()
    assert order["status"] == "rejected"
    assert "insufficient funds" in order["rejection_reason"]

    db.refresh(account)
    assert account.cash_balance == Decimal("50.00")
    assert account.cash_reserved == Decimal("0.00")


def test_sell_order_rejected_for_insufficient_shares(client, db):
    user, account = _funded_investor(db, "shortseller@x.com")
    instrument = _instrument(db, "NVDA", "100.00")
    token = _login(client, "shortseller@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "sell", "order_type": "market", "quantity": "5"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "rejected"
    assert "insufficient shares" in r.json()["rejection_reason"]


def test_order_rejected_when_kyc_not_validated(client, db):
    user = User(email="nokyc@x.com", password_hash=hash_password("StrongPass123!"), full_name="No Kyc", role=RoleEnum.investor)
    db.add(user)
    db.flush()
    account = Account(user_id=user.id, status=AccountStatus.active, cash_balance=Decimal("10000"))
    db.add(account)
    db.commit()

    instrument = _instrument(db, "META", "100.00")
    token = _login(client, "nokyc@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "1"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "rejected"
    assert "KYC" in r.json()["rejection_reason"]


def test_order_rejected_when_instrument_not_tradable(client, db):
    user, account = _funded_investor(db, "buyer2@x.com")
    instrument = _instrument(db, "OLDCO", "10.00", tradable=False)
    token = _login(client, "buyer2@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "1"},
    )
    assert r.status_code == 201
    assert r.json()["status"] == "rejected"
    assert "not tradable" in r.json()["rejection_reason"]


def test_limit_buy_not_satisfiable_is_rejected_and_releases_reservation(client, db):
    user, account = _funded_investor(db, "limitbuyer@x.com")
    instrument = _instrument(db, "GOOGL", "100.00")
    token = _login(client, "limitbuyer@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "limit",
              "quantity": "1", "limit_price": "90.00"},  # market is 100, limit buy at 90 unsatisfiable
    )
    assert r.status_code == 201
    order = r.json()
    assert order["status"] == "rejected"
    assert "not satisfiable" in order["rejection_reason"]

    db.refresh(account)
    assert account.cash_reserved == Decimal("0.00")  # reservation was fully released


def test_limit_buy_satisfiable_executes_at_market_price(client, db):
    user, account = _funded_investor(db, "limitbuyer2@x.com")
    instrument = _instrument(db, "AMZN", "100.00")
    token = _login(client, "limitbuyer2@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "limit",
              "quantity": "1", "limit_price": "110.00"},  # market 100 <= limit 110, satisfiable
    )
    assert r.status_code == 201
    assert r.json()["status"] == "executed"


def test_invalid_order_payload_is_422(client, db):
    user, account = _funded_investor(db, "buyer3@x.com")
    instrument = _instrument(db, "INTC", "10.00")
    token = _login(client, "buyer3@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "limit", "quantity": "1"},
    )
    assert r.status_code == 422  # limit_price required for limit orders


def test_list_and_get_orders_scoped_to_own_account(client, db):
    user1, account1 = _funded_investor(db, "scopeduser1@x.com")
    user2, account2 = _funded_investor(db, "scopeduser2@x.com")
    instrument = _instrument(db, "JPM", "50.00")

    token1 = _login(client, "scopeduser1@x.com")
    headers1 = {"Authorization": f"Bearer {token1}"}
    r = client.post(
        "/api/v1/orders", headers=headers1,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "1"},
    )
    order_id = r.json()["id"]

    r = client.get("/api/v1/orders", headers=headers1)
    assert r.status_code == 200
    assert len(r.json()) == 1

    token2 = _login(client, "scopeduser2@x.com")
    headers2 = {"Authorization": f"Bearer {token2}"}
    r = client.get("/api/v1/orders", headers=headers2)
    assert r.json() == []

    r = client.get(f"/api/v1/orders/{order_id}", headers=headers2)
    assert r.status_code == 404  # another user's order is invisible, not just forbidden


def test_cancel_reserved_order_releases_cash_reservation(client, db):
    # Synchronous execution means an order only ever transiently visits `reserved`
    # (submit_order resolves it to executed/rejected in the same request), so to
    # exercise cancel() we construct a `reserved` order + active reservation
    # directly, exactly as submit_order would leave it mid-flight.
    user, account = _funded_investor(db, "canceller@x.com", cash="5000.00")
    instrument = _instrument(db, "V", "100.00")

    order = Order(
        account_id=account.id, instrument_id=instrument.id, side=OrderSide.buy, order_type=OrderType.market,
        quantity=Decimal("10"), estimated_amount=Decimal("1000.00"), estimated_fees=Decimal("1.00"),
        status=OrderStatus.reserved,
    )
    db.add(order)
    db.flush()
    account.cash_reserved += Decimal("1001.00")
    db.add(Reservation(order_id=order.id, account_id=account.id, kind=ReservationKind.cash,
                        amount=Decimal("1001.00"), status=ReservationStatus.active))
    db.commit()
    db.refresh(account)
    assert account.cash_reserved == Decimal("1001.00")

    token = _login(client, "canceller@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(f"/api/v1/orders/{order.id}/cancel", headers=headers)
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"

    db.refresh(account)
    assert account.cash_reserved == Decimal("0.00")

    reservation = db.query(Reservation).filter(Reservation.order_id == order.id).one()
    assert reservation.status == ReservationStatus.released
    assert reservation.released_at is not None


def test_cancel_already_executed_order_fails(client, db):
    user, account = _funded_investor(db, "cantcancel@x.com")
    instrument = _instrument(db, "KO", "50.00")
    token = _login(client, "cantcancel@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "1"},
    )
    order_id = r.json()["id"]
    assert r.json()["status"] == "executed"

    r = client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert r.status_code == 409
