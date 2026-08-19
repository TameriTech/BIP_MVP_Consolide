import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import LedgerEntryType


class LedgerEntryOut(BaseModel):
    id: int
    reference: str
    account_id: uuid.UUID
    entry_type: LedgerEntryType
    amount: Decimal
    currency: str
    balance_after: Decimal
    order_id: uuid.UUID | None
    execution_id: uuid.UUID | None
    instrument_id: uuid.UUID | None
    created_at: datetime
    note: str | None

    model_config = {"from_attributes": True}
