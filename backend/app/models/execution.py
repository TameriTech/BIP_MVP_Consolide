import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPKMixin


class Execution(UUIDPKMixin, Base):
    __tablename__ = "executions"

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
