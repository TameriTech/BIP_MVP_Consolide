from datetime import datetime, timezone
from decimal import Decimal

from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.instrument import Instrument
from app.models.quote import Quote
from app.models.user import User


def _seed_instrument(db, symbol="AAPL", tradable=True):
    instrument = Instrument(
        symbol=symbol, name="Apple Inc.", market="DEMO", sector="Technology", currency="USD",
        tradable=tradable, last_price=Decimal("230.50"), last_price_at=datetime.now(timezone.utc),
    )
    db.add(instrument)
    db.flush()
    db.add(Quote(instrument_id=instrument.id, price=Decimal("230.50"), as_of=datetime.now(timezone.utc),
                  source="fallback_seed", close=Decimal("230.50")))
    db.commit()
    db.refresh(instrument)
    return instrument


def _admin_token(client, db):
    user = User(email="admin@x.com", password_hash=hash_password("StrongPass123!"), full_name="Admin",
                role=RoleEnum.admin)
    db.add(user)
    db.commit()
    r = client.post("/api/v1/auth/login", json={"email": "admin@x.com", "password": "StrongPass123!"})
    return r.json()["access_token"]


def test_list_and_get_instrument(client, db):
    _seed_instrument(db, "AAPL")
    _seed_instrument(db, "MSFT")

    r = client.get("/api/v1/instruments")
    assert r.status_code == 200
    symbols = {i["symbol"] for i in r.json()}
    assert symbols == {"AAPL", "MSFT"}

    r = client.get("/api/v1/instruments/AAPL")
    assert r.status_code == 200
    assert r.json()["last_price"] == "230.500000"


def test_get_unknown_instrument_404(client):
    r = client.get("/api/v1/instruments/NOPE")
    assert r.status_code == 404


def test_filter_by_tradable(client, db):
    _seed_instrument(db, "AAPL", tradable=True)
    _seed_instrument(db, "OLD", tradable=False)

    r = client.get("/api/v1/instruments?tradable=false")
    assert r.status_code == 200
    assert [i["symbol"] for i in r.json()] == ["OLD"]


def test_latest_and_history_quotes(client, db):
    _seed_instrument(db, "AAPL")

    r = client.get("/api/v1/instruments/AAPL/quote")
    assert r.status_code == 200
    assert r.json()["price"] == "230.500000"

    r = client.get("/api/v1/instruments/AAPL/quotes")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_backoffice_create_and_patch_instrument(client, db):
    token = _admin_token(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/backoffice/instruments",
        headers=headers,
        json={"symbol": "baba", "name": "Alibaba", "sector": "Technology"},
    )
    assert r.status_code == 201
    assert r.json()["symbol"] == "BABA"  # normalized to uppercase
    instrument_id = r.json()["id"]

    r = client.post(
        "/api/v1/backoffice/instruments",
        headers=headers,
        json={"symbol": "BABA", "name": "Alibaba dup"},
    )
    assert r.status_code == 409

    r = client.patch(f"/api/v1/backoffice/instruments/{instrument_id}", headers=headers, json={"tradable": False})
    assert r.status_code == 200
    assert r.json()["tradable"] is False


def test_investor_forbidden_from_creating_instrument(client):
    r = client.post("/api/v1/auth/register", json={"email": "inv@x.com", "password": "StrongPass123!", "full_name": "Inv"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.post("/api/v1/backoffice/instruments", headers=headers, json={"symbol": "X", "name": "X"})
    assert r.status_code == 403


def test_manual_refresh_never_crashes_even_if_yfinance_unreachable(client, db, monkeypatch):
    _seed_instrument(db, "AAPL")
    token = _admin_token(client, db)

    from app.services import market_data_service
    monkeypatch.setattr(market_data_service, "_download", lambda symbols, period, interval: None)

    r = client.post("/api/v1/backoffice/market/refresh", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "yfinance_unavailable"
