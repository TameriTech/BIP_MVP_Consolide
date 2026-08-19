import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import KycStatus


class KycUpsertRequest(BaseModel):
    full_legal_name: str | None = Field(default=None, max_length=255)
    birth_date: date | None = None
    country: str | None = Field(default=None, max_length=2)
    id_document_type: str | None = Field(default=None, max_length=50)
    id_document_number: str | None = Field(default=None, max_length=100)
    extra: dict | None = None


class KycRejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class KycOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    status: KycStatus
    full_legal_name: str | None
    birth_date: date | None
    country: str | None
    id_document_type: str | None
    id_document_number: str | None
    rejection_reason: str | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
