from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Instrument(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "instruments"

    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    market: Mapped[str] = mapped_column(String(50), nullable=False, default="DEMO")
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    tradable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    last_price_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
