from decimal import ROUND_HALF_UP, Decimal

from app.core.config import settings


def compute(gross_amount: Decimal) -> Decimal:
    rate = Decimal(settings.fee_rate_bps) / Decimal(10000)
    return (gross_amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
