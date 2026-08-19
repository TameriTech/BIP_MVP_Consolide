from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.schemas.portfolio import PerformanceOut, PortfolioOut, PositionView
from app.services import account_service, portfolio_service

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/me", response_model=PortfolioOut)
def get_my_portfolio(db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    return portfolio_service.get_portfolio(db, account)


@router.get("/me/positions", response_model=list[PositionView])
def get_my_positions(db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    return portfolio_service.get_portfolio(db, account)["positions"]


@router.get("/me/performance", response_model=PerformanceOut)
def get_my_performance(db: DbSession, user: CurrentUser):
    account = account_service.get_account_for_user(db, user)
    return portfolio_service.get_performance(db, account)
