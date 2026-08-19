from datetime import datetime

from fastapi import APIRouter

from app.core.deps import DbSession
from app.schemas.market import InstrumentOut, QuoteOut
from app.services import market_service

router = APIRouter(prefix="/instruments", tags=["market"])


@router.get("", response_model=list[InstrumentOut])
def list_instruments(
    db: DbSession, market: str | None = None, sector: str | None = None, tradable: bool | None = None
):
    return market_service.list_instruments(db, market, sector, tradable)


@router.get("/{symbol}", response_model=InstrumentOut)
def get_instrument(symbol: str, db: DbSession):
    return market_service.get_instrument_by_symbol(db, symbol)


@router.get("/{symbol}/quote", response_model=QuoteOut | None)
def get_latest_quote(symbol: str, db: DbSession):
    instrument = market_service.get_instrument_by_symbol(db, symbol)
    return market_service.get_latest_quote(db, instrument)


@router.get("/{symbol}/quotes", response_model=list[QuoteOut])
def get_quotes(symbol: str, db: DbSession, date_from: datetime | None = None, date_to: datetime | None = None):
    instrument = market_service.get_instrument_by_symbol(db, symbol)
    return market_service.list_quotes(db, instrument, date_from, date_to)
