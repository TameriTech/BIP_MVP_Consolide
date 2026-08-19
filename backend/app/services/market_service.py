import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.instrument import Instrument
from app.models.quote import Quote


def list_instruments(
    db: Session, market: str | None = None, sector: str | None = None, tradable: bool | None = None
) -> list[Instrument]:
    query = db.query(Instrument)
    if market is not None:
        query = query.filter(Instrument.market == market)
    if sector is not None:
        query = query.filter(Instrument.sector == sector)
    if tradable is not None:
        query = query.filter(Instrument.tradable == tradable)
    return query.order_by(Instrument.symbol).all()


def get_instrument_by_symbol(db: Session, symbol: str) -> Instrument:
    instrument = db.query(Instrument).filter(Instrument.symbol == symbol.upper()).first()
    if instrument is None:
        raise NotFoundError("instrument not found")
    return instrument


def get_instrument_by_id(db: Session, instrument_id: uuid.UUID) -> Instrument:
    instrument = db.get(Instrument, instrument_id)
    if instrument is None:
        raise NotFoundError("instrument not found")
    return instrument


def list_quotes(
    db: Session, instrument: Instrument, date_from: datetime | None = None, date_to: datetime | None = None
) -> list[Quote]:
    query = db.query(Quote).filter(Quote.instrument_id == instrument.id)
    if date_from is not None:
        query = query.filter(Quote.as_of >= date_from)
    if date_to is not None:
        query = query.filter(Quote.as_of <= date_to)
    return query.order_by(Quote.as_of).all()


def get_latest_quote(db: Session, instrument: Instrument) -> Quote | None:
    return (
        db.query(Quote)
        .filter(Quote.instrument_id == instrument.id)
        .order_by(Quote.as_of.desc())
        .first()
    )


def create_instrument(db: Session, data: dict) -> Instrument:
    existing = db.query(Instrument).filter(Instrument.symbol == data["symbol"].upper()).first()
    if existing is not None:
        raise ConflictError("an instrument with this symbol already exists", {"field": "symbol"})
    instrument = Instrument(**{**data, "symbol": data["symbol"].upper()})
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


def update_instrument(db: Session, instrument: Instrument, data: dict) -> Instrument:
    for field, value in data.items():
        if value is not None:
            setattr(instrument, field, value)
    db.commit()
    db.refresh(instrument)
    return instrument
