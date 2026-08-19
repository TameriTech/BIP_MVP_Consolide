import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class InstrumentOut(BaseModel):
    id: uuid.UUID
    symbol: str
    name: str
    market: str
    sector: str | None
    currency: str
    tradable: bool
    last_price: Decimal | None
    last_price_at: datetime | None

    model_config = {"from_attributes": True}


class InstrumentCreateRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=255)
    market: str = Field(default="DEMO", max_length=50)
    sector: str | None = Field(default=None, max_length=100)
    currency: str = Field(default="USD", max_length=3)


class InstrumentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    sector: str | None = Field(default=None, max_length=100)
    tradable: bool | None = None


class QuoteOut(BaseModel):
    price: Decimal
    as_of: datetime
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: int | None
    source: str

    model_config = {"from_attributes": True}
