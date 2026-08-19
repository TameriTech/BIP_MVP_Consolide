"""Base seed: demo users (one per role) and the instrument catalog.

Idempotent — safe to run multiple times. Run with `python -m app.seed`.
"""

from datetime import datetime, timezone
from decimal import Decimal

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.account import Account
from app.models.enums import AccountStatus, RoleEnum
from app.models.instrument import Instrument
from app.models.quote import Quote
from app.models.user import User

DEMO_USERS = [
    ("investor@bip.demo", "Demo Investor", RoleEnum.investor),
    ("admin@bip.demo", "Demo Admin", RoleEnum.admin),
    ("backoffice@bip.demo", "Demo Backoffice", RoleEnum.backoffice_operator),
    ("superadmin@bip.demo", "Demo Super Admin", RoleEnum.super_admin),
]
DEMO_PASSWORD = "DemoPass123!"

INSTRUMENTS = [
    ("AAPL", "Apple Inc.", "Technology"),
    ("MSFT", "Microsoft Corporation", "Technology"),
    ("GOOGL", "Alphabet Inc.", "Technology"),
    ("AMZN", "Amazon.com Inc.", "Consumer Discretionary"),
    ("TSLA", "Tesla Inc.", "Consumer Discretionary"),
    ("NVDA", "NVIDIA Corporation", "Technology"),
    ("META", "Meta Platforms Inc.", "Technology"),
    ("JPM", "JPMorgan Chase & Co.", "Financials"),
    ("V", "Visa Inc.", "Financials"),
    ("KO", "The Coca-Cola Company", "Consumer Staples"),
    ("JNJ", "Johnson & Johnson", "Healthcare"),
    ("WMT", "Walmart Inc.", "Consumer Staples"),
    ("PG", "Procter & Gamble Co.", "Consumer Staples"),
    ("DIS", "The Walt Disney Company", "Communication Services"),
    ("NFLX", "Netflix Inc.", "Communication Services"),
    ("PFE", "Pfizer Inc.", "Healthcare"),
    ("XOM", "Exxon Mobil Corporation", "Energy"),
    ("INTC", "Intel Corporation", "Technology"),
]

# Plausible baseline prices so the platform is fully usable even if yfinance
# is unreachable (rate-limited datacenter IPs, offline demo venue, etc). This
# is what guarantees the demo never depends on live internet access.
FALLBACK_PRICES: dict[str, str] = {
    "AAPL": "230.50", "MSFT": "430.20", "GOOGL": "175.80", "AMZN": "200.10",
    "TSLA": "250.75", "NVDA": "140.30", "META": "580.40", "JPM": "230.60",
    "V": "310.90", "KO": "63.20", "JNJ": "155.40", "WMT": "90.10",
    "PG": "165.30", "DIS": "110.20", "NFLX": "700.50", "PFE": "26.40",
    "XOM": "115.60", "INTC": "22.30",
}


def seed_users(db) -> None:
    for email, full_name, role in DEMO_USERS:
        user = db.query(User).filter(User.email == email).first()
        if user is not None:
            continue
        user = User(email=email, password_hash=hash_password(DEMO_PASSWORD), full_name=full_name, role=role)
        db.add(user)
        db.flush()
        db.add(Account(user_id=user.id, status=AccountStatus.pending))
    db.commit()


def seed_instruments(db) -> None:
    now = datetime.now(timezone.utc)
    for symbol, name, sector in INSTRUMENTS:
        existing = db.query(Instrument).filter(Instrument.symbol == symbol).first()
        if existing is not None:
            continue
        price = Decimal(FALLBACK_PRICES[symbol])
        instrument = Instrument(
            symbol=symbol, name=name, market="DEMO", sector=sector, currency="USD",
            tradable=True, last_price=price, last_price_at=now,
        )
        db.add(instrument)
        db.flush()
        db.add(Quote(instrument_id=instrument.id, price=price, as_of=now, source="fallback_seed", close=price))
    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        seed_users(db)
        seed_instruments(db)
        print(f"Seeded {len(DEMO_USERS)} demo users and {len(INSTRUMENTS)} instruments.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
