import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LedgerEntryType


class LedgerEntry(Base):
    """Append-only source of truth for all financial movements.

    No update/delete is ever exposed for this table anywhere in the codebase —
    corrections must be new, offsetting entries, never mutations.
    """

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    entry_type: Mapped[LedgerEntryType] = mapped_column(
        Enum(LedgerEntryType, name="ledger_entry_type"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)  # signed: credit>0, debit<0
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executions.id"), nullable=True
    )
    instrument_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
