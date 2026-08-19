from datetime import datetime

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.models.enums import LedgerEntryType
from app.schemas.ledger import LedgerEntryOut
from app.services import account_service, ledger_service

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/me", response_model=list[LedgerEntryOut])
def get_my_ledger(
    db: DbSession, user: CurrentUser, date_from: datetime | None = None, date_to: datetime | None = None,
    entry_type: LedgerEntryType | None = None,
):
    account = account_service.get_account_for_user(db, user)
    return ledger_service.list_ledger_entries(db, account.id, date_from, date_to, entry_type)
