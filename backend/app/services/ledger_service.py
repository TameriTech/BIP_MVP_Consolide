import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.enums import LedgerEntryType
from app.models.ledger import LedgerEntry


def list_ledger_entries(
    db: Session,
    account_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    entry_type: LedgerEntryType | None = None,
) -> list[LedgerEntry]:
    query = db.query(LedgerEntry)
    if account_id is not None:
        query = query.filter(LedgerEntry.account_id == account_id)
    if date_from is not None:
        query = query.filter(LedgerEntry.created_at >= date_from)
    if date_to is not None:
        query = query.filter(LedgerEntry.created_at <= date_to)
    if entry_type is not None:
        query = query.filter(LedgerEntry.entry_type == entry_type)
    return query.order_by(LedgerEntry.created_at.desc()).all()
