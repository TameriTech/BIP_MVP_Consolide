from datetime import datetime, timezone
from decimal import Decimal

from app.core.security import hash_password
from app.engine import ledger_writer
from app.models.account import Account
from app.models.enums import AccountStatus, KycStatus, LedgerEntryType, RoleEnum
from app.models.instrument import Instrument
from app.models.kyc import KycFile
from app.models.user import User


def make_funded_account(db, email: str, cash: str = "1000.00"):
    """A validated, active account funded via a real ledger entry — mirrors
    exactly what kyc_service.validate_kyc does in production, so invariants
    like `cash_balance == sum(ledger_entries.amount)` hold from account
    creation rather than being an artifact of test setup.
    """
    user = User(email=email, password_hash=hash_password("StrongPass123!"), full_name="Test", role=RoleEnum.investor)
    db.add(user)
    db.flush()
    account = Account(user_id=user.id, status=AccountStatus.active, cash_balance=Decimal("0"),
                       activated_at=datetime.now(timezone.utc))
    db.add(account)
    db.flush()
    db.add(KycFile(account_id=account.id, status=KycStatus.validated, full_legal_name="Test",
                    id_document_number="X", reviewed_at=datetime.now(timezone.utc)))
    account.cash_balance = Decimal(cash)
    ledger_writer.append(db, account=account, entry_type=LedgerEntryType.initial_credit, amount=Decimal(cash))
    db.commit()
    db.refresh(account)
    return user, account


def make_instrument(db, symbol: str, price: str = "100.00", tradable: bool = True):
    instrument = Instrument(symbol=symbol, name=symbol, market="DEMO", currency="USD", tradable=tradable,
                             last_price=Decimal(price), last_price_at=datetime.now(timezone.utc))
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument
