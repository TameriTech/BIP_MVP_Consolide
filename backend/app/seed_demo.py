"""Rich demo dataset on top of the base seed — a ready-to-present state.

Guarantees the "everything already works" path never depends on a live
action during the pitch: the demo investor is already KYC-validated,
funded, and holds a realistic portfolio with executed order history.

Idempotent — safe to run multiple times. Run with `python -m app.seed_demo`.
(Runs the base seed first, so a single command is enough on a clean DB.)
"""

from decimal import Decimal

from app.db.session import SessionLocal
from app.models.account import Account
from app.models.enums import KycStatus, OrderSide, OrderStatus, OrderType
from app.models.instrument import Instrument
from app.models.kyc import KycFile
from app.models.order import Order
from app.models.user import User
from app.seed import run as run_base_seed
from app.services import kyc_service, order_service

DEMO_INVESTOR_EMAIL = "investor@bip.demo"
REVIEWER_EMAIL = "backoffice@bip.demo"

SAMPLE_TRADES = [
    ("AAPL", OrderSide.buy, "20"),
    ("MSFT", OrderSide.buy, "10"),
    ("TSLA", OrderSide.buy, "8"),
    ("KO", OrderSide.buy, "50"),
    ("AAPL", OrderSide.sell, "5"),
]


def ensure_demo_investor_validated(db) -> Account:
    investor = db.query(User).filter(User.email == DEMO_INVESTOR_EMAIL).one()
    account = db.query(Account).filter(Account.user_id == investor.id).one()
    kyc = kyc_service.get_or_create_kyc(db, account)

    if kyc.status == KycStatus.validated:
        return account

    reviewer = db.query(User).filter(User.email == REVIEWER_EMAIL).one()

    if kyc.status in (KycStatus.draft, KycStatus.rejected):
        kyc = kyc_service.upsert_draft(
            db, account,
            {
                "full_legal_name": "Demo Investor",
                "id_document_type": "passport",
                "id_document_number": "DEMO-0001",
                "country": "CI",
            },
        )
        kyc = kyc_service.submit_kyc(db, account, investor)

    kyc_service.validate_kyc(db, kyc, reviewer)
    db.refresh(account)
    return account


def place_sample_trades(db, account: Account) -> int:
    placed = 0
    for symbol, side, quantity in SAMPLE_TRADES:
        instrument = db.query(Instrument).filter(Instrument.symbol == symbol).one()
        order = order_service.submit_order(
            db, account, instrument.id, side, OrderType.market, Decimal(quantity), None,
        )
        if order.status == OrderStatus.executed:
            placed += 1
    return placed


def already_has_sample_orders(db, account: Account) -> bool:
    return db.query(Order).filter(Order.account_id == account.id).count() > 0


def run() -> None:
    run_base_seed()

    db = SessionLocal()
    try:
        account = ensure_demo_investor_validated(db)
        if already_has_sample_orders(db, account):
            print("Demo investor already has order history — skipping sample trades.")
        else:
            placed = place_sample_trades(db, account)
            print(f"Placed {placed} sample trade(s) for {DEMO_INVESTOR_EMAIL}.")
        db.refresh(account)
        print(f"Demo investor ready: status={account.status.value}, cash_balance={account.cash_balance}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
