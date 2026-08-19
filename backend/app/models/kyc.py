import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import KycStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class KycFile(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "kyc_files"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), unique=True, nullable=False
    )
    status: Mapped[KycStatus] = mapped_column(
        Enum(KycStatus, name="kyc_status"), nullable=False, default=KycStatus.draft
    )
    full_legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    id_document_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    id_document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    history: Mapped[list["KycStatusHistory"]] = relationship(
        back_populates="kyc_file", order_by="KycStatusHistory.changed_at"
    )


class KycStatusHistory(UUIDPKMixin, Base):
    __tablename__ = "kyc_status_history"

    kyc_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kyc_files.id"), nullable=False
    )
    from_status: Mapped[KycStatus | None] = mapped_column(Enum(KycStatus, name="kyc_status"), nullable=True)
    to_status: Mapped[KycStatus] = mapped_column(Enum(KycStatus, name="kyc_status"), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    kyc_file: Mapped["KycFile"] = relationship(back_populates="history")
