from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.engine import ledger_writer
from app.models.account import Account
from app.models.enums import AccountStatus, KycStatus, LedgerEntryType
from app.models.kyc import KycFile, KycStatusHistory
from app.models.user import User
from app.services import audit_service

_EDITABLE_STATUSES = (KycStatus.draft, KycStatus.rejected)
_KYC_FIELDS = (
    "full_legal_name",
    "birth_date",
    "country",
    "id_document_type",
    "id_document_number",
    "extra",
)


def get_or_create_kyc(db: Session, account: Account) -> KycFile:
    kyc = db.query(KycFile).filter(KycFile.account_id == account.id).first()
    if kyc is None:
        kyc = KycFile(account_id=account.id, status=KycStatus.draft)
        db.add(kyc)
        db.commit()
        db.refresh(kyc)
    return kyc


def _record_transition(
    db: Session, kyc: KycFile, to_status: KycStatus, changed_by, note: str | None = None
) -> None:
    db.add(
        KycStatusHistory(
            kyc_file_id=kyc.id,
            from_status=kyc.status,
            to_status=to_status,
            changed_by=changed_by,
            changed_at=datetime.now(timezone.utc),
            note=note,
        )
    )
    kyc.status = to_status


def get_kyc_by_id(db: Session, kyc_id) -> KycFile:
    kyc = db.get(KycFile, kyc_id)
    if kyc is None:
        raise NotFoundError("KYC file not found")
    return kyc


def list_kyc(db: Session, status_filter: KycStatus | None = None) -> list[KycFile]:
    query = db.query(KycFile)
    if status_filter is not None:
        query = query.filter(KycFile.status == status_filter)
    return query.order_by(KycFile.created_at.desc()).all()


def upsert_draft(db: Session, account: Account, data: dict) -> KycFile:
    kyc = get_or_create_kyc(db, account)
    if kyc.status not in _EDITABLE_STATUSES:
        raise ConflictError("KYC file cannot be edited in its current status", {"status": kyc.status.value})

    was_rejected = kyc.status == KycStatus.rejected
    for field in _KYC_FIELDS:
        if field in data and data[field] is not None:
            setattr(kyc, field, data[field])
    if was_rejected:
        kyc.rejection_reason = None
        _record_transition(db, kyc, KycStatus.draft, changed_by=None, note="edited after rejection")

    db.commit()
    db.refresh(kyc)
    return kyc


def submit_kyc(db: Session, account: Account, user: User) -> KycFile:
    kyc = get_or_create_kyc(db, account)
    if kyc.status != KycStatus.draft:
        raise ConflictError("KYC file must be in draft status to submit", {"status": kyc.status.value})
    if not kyc.full_legal_name or not kyc.id_document_number:
        raise ValidationAppError("KYC file is missing required fields")

    kyc.submitted_at = datetime.now(timezone.utc)
    _record_transition(db, kyc, KycStatus.submitted, changed_by=user.id)
    db.commit()
    db.refresh(kyc)
    return kyc


def validate_kyc(db: Session, kyc: KycFile, reviewer: User) -> KycFile:
    """Validates the KYC file and, in the SAME transaction, activates the
    account and grants the initial simulated cash credit — the doc's own
    §8 parcours (KYC validated → account active → funded) modeled as one
    atomic step so a partially-activated, unfunded account can never exist.
    """
    if kyc.status != KycStatus.submitted:
        raise ConflictError("KYC file must be submitted to validate", {"status": kyc.status.value})

    kyc.reviewed_at = datetime.now(timezone.utc)
    kyc.reviewed_by = reviewer.id
    _record_transition(db, kyc, KycStatus.validated, changed_by=reviewer.id)

    account = db.get(Account, kyc.account_id)
    account.status = AccountStatus.active
    account.activated_at = datetime.now(timezone.utc)

    initial_credit = Decimal(settings.initial_credit_amount)
    account.cash_balance += initial_credit
    ledger_writer.append(
        db,
        account=account,
        entry_type=LedgerEntryType.initial_credit,
        amount=initial_credit,
        created_by=reviewer.id,
        note="initial simulated credit on KYC validation",
    )
    audit_service.log(
        db, actor_user_id=reviewer.id, actor_role=reviewer.role.value, action="kyc.validate",
        entity_type="kyc_file", entity_id=kyc.id, metadata={"account_id": str(account.id)},
    )

    db.commit()
    db.refresh(kyc)
    return kyc


def reject_kyc(db: Session, kyc: KycFile, reviewer: User, reason: str) -> KycFile:
    if kyc.status != KycStatus.submitted:
        raise ConflictError("KYC file must be submitted to reject", {"status": kyc.status.value})

    kyc.reviewed_at = datetime.now(timezone.utc)
    kyc.reviewed_by = reviewer.id
    kyc.rejection_reason = reason
    _record_transition(db, kyc, KycStatus.rejected, changed_by=reviewer.id, note=reason)
    audit_service.log(
        db, actor_user_id=reviewer.id, actor_role=reviewer.role.value, action="kyc.reject",
        entity_type="kyc_file", entity_id=kyc.id, metadata={"reason": reason},
    )

    db.commit()
    db.refresh(kyc)
    return kyc
