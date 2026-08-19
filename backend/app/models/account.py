import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AccountStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Account(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("cash_balance >= 0", name="ck_accounts_cash_balance_nonneg"),
        CheckConstraint("cash_reserved >= 0", name="ck_accounts_cash_reserved_nonneg"),
        CheckConstraint("cash_reserved <= cash_balance", name="ck_accounts_reserved_le_balance"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status"), nullable=False, default=AccountStatus.pending
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    cash_reserved: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="account")
