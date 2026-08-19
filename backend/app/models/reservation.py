import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ReservationKind, ReservationStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Reservation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "reservations"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), unique=True, nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    kind: Mapped[ReservationKind] = mapped_column(Enum(ReservationKind, name="reservation_kind"), nullable=False)
    instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=True
    )
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, name="reservation_status"), nullable=False, default=ReservationStatus.active
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
