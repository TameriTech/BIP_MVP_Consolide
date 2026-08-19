from datetime import datetime, timezone
from decimal import Decimal

from app.models.position import Position
from tests.api.test_orders import _funded_investor, _instrument, _login


def test_portfolio_reflects_cash_and_positions(client, db):
    user, account = _funded_investor(db, "portfolio1@x.com", cash="5000.00")
    instrument = _instrument(db, "PORT1", "50.00")
    position = Position(account_id=account.id, instrument_id=instrument.id, quantity=Decimal("10"), avg_cost=Decimal("40"))
    db.add(position)
    db.commit()

    token = _login(client, "portfolio1@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/portfolio/me", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["cash_balance"] == "5000.00"
    assert body["positions_value"] == "500.00"  # 10 * 50.00
    assert body["total_value"] == "5500.00"
    assert len(body["positions"]) == 1
    assert body["positions"][0]["symbol"] == "PORT1"

    r = client.get("/api/v1/portfolio/me/positions", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get("/api/v1/portfolio/me/performance", headers=headers)
    assert r.status_code == 200
    perf = r.json()
    # avg_cost 40, last_price 50, qty 10 -> unrealized pl = 100
    assert perf["unrealized_pl"] == "100.00" or float(perf["unrealized_pl"]) == 100.0


def test_portfolio_empty_when_no_positions(client, db):
    user, account = _funded_investor(db, "portfolio2@x.com", cash="1000.00")
    token = _login(client, "portfolio2@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/portfolio/me", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["positions"] == []
    assert body["total_value"] == "1000.00"


def test_my_ledger_reflects_trades(client, db):
    user, account = _funded_investor(db, "ledger1@x.com", cash="2000.00")
    instrument = _instrument(db, "LEDG1", "20.00")
    token = _login(client, "ledger1@x.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/orders", headers=headers,
        json={"instrument_id": str(instrument.id), "side": "buy", "order_type": "market", "quantity": "5"},
    )
    assert r.json()["status"] == "executed"

    r = client.get("/api/v1/ledger/me", headers=headers)
    assert r.status_code == 200
    entries = r.json()
    # initial_credit + trade_buy + fee
    assert len(entries) == 3
    assert {e["entry_type"] for e in entries} == {"initial_credit", "trade_buy", "fee"}


def test_ledger_scoped_to_own_account(client, db):
    user1, account1 = _funded_investor(db, "ledgeruser1@x.com")
    user2, account2 = _funded_investor(db, "ledgeruser2@x.com")

    token2 = _login(client, "ledgeruser2@x.com")
    headers2 = {"Authorization": f"Bearer {token2}"}
    r = client.get("/api/v1/ledger/me", headers=headers2)
    assert r.status_code == 200
    assert len(r.json()) == 1  # only their own initial_credit entry
