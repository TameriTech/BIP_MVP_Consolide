import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Position(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("account_id", "instrument_id", name="uq_positions_account_instrument"),
        CheckConstraint("quantity >= 0", name="ck_positions_quantity_nonneg"),
        CheckConstraint("reserved_quantity >= 0", name="ck_positions_reserved_nonneg"),
        CheckConstraint("reserved_quantity <= quantity", name="ck_positions_reserved_le_quantity"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=0)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=0)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=0)
