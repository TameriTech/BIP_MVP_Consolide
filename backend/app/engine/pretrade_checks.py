"""Pre-trade checks (doc §16). Pure evaluation — returns a rejection reason
string, or None if every check passes. Never raises for a business rejection;
the caller is responsible for turning a non-None reason into a rejected Order.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import AccountStatus, KycStatus, OrderType
from app.models.instrument import Instrument
from app.models.kyc import KycFile


def evaluate(
    db: Session, account: Account, instrument: Instrument, order_type: OrderType, limit_price: Decimal | None
) -> str | None:
    if account.status != AccountStatus.active:
        return f"account is not active (status: {account.status.value})"

    kyc = db.query(KycFile).filter(KycFile.account_id == account.id).first()
    if kyc is None or kyc.status != KycStatus.validated:
        return "KYC has not been validated for this account"

    if not instrument.tradable:
        return f"instrument {instrument.symbol} is not tradable"

    if order_type == OrderType.limit and (limit_price is None or limit_price <= 0):
        return "a positive limit price is required for limit orders"

    if order_type == OrderType.market and instrument.last_price is None:
        return "no reference price is available for this instrument"

    return None
