from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.kyc import KycOut, KycUpsertRequest
from app.services import account_service, kyc_service

router = APIRouter(prefix="/kyc", tags=["kyc"])


@router.get("/me", response_model=KycOut)
def get_my_kyc(db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    return kyc_service.get_or_create_kyc(db, account)


@router.post("/me", response_model=KycOut)
def upsert_my_kyc(data: KycUpsertRequest, db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    return kyc_service.upsert_draft(db, account, data.model_dump(exclude_unset=True))


@router.post("/me/submit", response_model=KycOut, status_code=status.HTTP_200_OK)
def submit_my_kyc(db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    return kyc_service.submit_kyc(db, account, user)
