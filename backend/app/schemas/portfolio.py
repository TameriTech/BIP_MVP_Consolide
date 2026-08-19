import uuid
from decimal import Decimal

from pydantic import BaseModel


class PositionView(BaseModel):
    instrument_id: uuid.UUID
    symbol: str
    quantity: Decimal
    reserved_quantity: Decimal
    avg_cost: Decimal
    last_price: Decimal | None
    market_value: Decimal


class PortfolioOut(BaseModel):
    cash_balance: Decimal
    cash_reserved: Decimal
    cash_available: Decimal
    positions_value: Decimal
    total_value: Decimal
    positions: list[PositionView]


class PerformanceOut(BaseModel):
    total_value: Decimal
    cost_basis: Decimal
    unrealized_pl: Decimal
    unrealized_pl_pct: Decimal
