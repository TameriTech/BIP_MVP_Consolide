"""Append-only writer for the ledger — the system's financial source of truth.

Deliberately exposes only `append`. There is no update/delete function here or
anywhere else in the codebase — corrections must be new, offsetting entries.
"""

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session
from ulid import ULID

from app.models.account import Account
from app.models.enums import LedgerEntryType
from app.models.ledger import LedgerEntry


def append(
    db: Session,
    *,
    account: Account,
    entry_type: LedgerEntryType,
    amount: Decimal,
    order_id: uuid.UUID | None = None,
    execution_id: uuid.UUID | None = None,
    instrument_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
    note: str | None = None,
) -> LedgerEntry:
    """Append an immutable entry for `amount` (signed: credit>0, debit<0).

    The caller must update `account.cash_balance` in the same transaction
    *before* calling this, so `balance_after` reflects the post-write balance.
    """
    entry = LedgerEntry(
        reference=str(ULID()),
        account_id=account.id,
        entry_type=entry_type,
        amount=amount,
        currency=account.currency,
        balance_after=account.cash_balance,
        order_id=order_id,
        execution_id=execution_id,
        instrument_id=instrument_id,
        created_by=created_by,
        note=note,
    )
    db.add(entry)
    db.flush()
    return entry
