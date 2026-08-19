import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (
        UniqueConstraint("instrument_id", "as_of", name="uq_quotes_instrument_as_of"),
        CheckConstraint("price > 0", name="ck_quotes_price_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False, index=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="yfinance")
    open: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    high: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    low: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    close: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
