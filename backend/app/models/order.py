import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import OrderSide, OrderStatus, OrderType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Order(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_orders_quantity_positive"),)

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    side: Mapped[OrderSide] = mapped_column(Enum(OrderSide, name="order_side"), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType, name="order_type"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    estimated_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    estimated_fees: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), nullable=False, default=OrderStatus.submitted
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
