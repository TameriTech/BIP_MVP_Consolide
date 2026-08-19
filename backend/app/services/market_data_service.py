"""Best-effort market data ingestion from yfinance.

Postgres (Instrument.last_price / Quote rows) is the actual source of truth
the rest of the app reads from — this module is purely an upstream feed.
Any yfinance failure (network, rate limiting, schema change) is caught here
and never propagates: the platform must keep working on whatever prices it
already has (seeded fallback or a previous successful fetch).
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.models.quote import Quote

logger = logging.getLogger("app.market_data")


def _to_decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _frame_for_symbol(data: pd.DataFrame, symbol: str, single_symbol: bool) -> pd.DataFrame | None:
    try:
        if single_symbol:
            return data
        if isinstance(data.columns, pd.MultiIndex):
            return data[symbol]
        return data
    except (KeyError, TypeError):
        return None


def _download(symbols: list[str], period: str, interval: str) -> pd.DataFrame | None:
    try:
        data = yf.download(
            symbols, period=period, interval=interval, group_by="ticker", progress=False, threads=True
        )
    except Exception:
        logger.warning("yfinance download failed for %s", symbols, exc_info=True)
        return None
    if data is None or data.empty:
        return None
    return data


def _upsert_row(db: Session, instrument: Instrument, as_of: datetime, row: pd.Series) -> bool:
    close = _to_decimal(row.get("Close"))
    if close is None or close <= 0:
        return False
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)

    exists = (
        db.query(Quote.id)
        .filter(Quote.instrument_id == instrument.id, Quote.as_of == as_of)
        .first()
    )
    inserted = exists is None
    if inserted:
        volume_raw = row.get("Volume")
        volume = int(volume_raw) if volume_raw is not None and not pd.isna(volume_raw) else None
        db.add(
            Quote(
                instrument_id=instrument.id,
                price=close,
                as_of=as_of,
                source="yfinance",
                open=_to_decimal(row.get("Open")),
                high=_to_decimal(row.get("High")),
                low=_to_decimal(row.get("Low")),
                close=close,
                volume=volume,
            )
        )
    instrument.last_price = close
    instrument.last_price_at = datetime.now(timezone.utc)
    return inserted


def backfill_history(db: Session, period: str = "3mo") -> dict:
    """One-time (or repeatable, idempotent) pull of daily history per instrument."""
    instruments = db.query(Instrument).all()
    if not instruments:
        return {"instruments": 0, "quotes_upserted": 0}

    symbol_map = {i.symbol: i for i in instruments}
    data = _download(list(symbol_map.keys()), period=period, interval="1d")
    if data is None:
        return {"instruments": len(instruments), "quotes_upserted": 0, "status": "yfinance_unavailable"}

    single = len(symbol_map) == 1
    upserted = 0
    for symbol, instrument in symbol_map.items():
        frame = _frame_for_symbol(data, symbol, single)
        if frame is None:
            continue
        frame = frame.dropna(how="all")
        for idx, row in frame.iterrows():
            as_of = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
            if _upsert_row(db, instrument, as_of, row):
                upserted += 1

    db.commit()
    return {"instruments": len(instruments), "quotes_upserted": upserted, "status": "ok"}


def refresh_latest(db: Session) -> dict:
    """Lightweight pull of the most recent price per instrument."""
    instruments = db.query(Instrument).all()
    if not instruments:
        return {"instruments": 0, "updated": 0}

    symbol_map = {i.symbol: i for i in instruments}
    data = _download(list(symbol_map.keys()), period="5d", interval="1d")
    if data is None:
        return {"instruments": len(instruments), "updated": 0, "status": "yfinance_unavailable"}

    single = len(symbol_map) == 1
    updated = 0
    for symbol, instrument in symbol_map.items():
        frame = _frame_for_symbol(data, symbol, single)
        if frame is None:
            continue
        frame = frame.dropna(how="all")
        if frame.empty:
            continue
        last_idx = frame.index[-1]
        as_of = last_idx.to_pydatetime() if hasattr(last_idx, "to_pydatetime") else last_idx
        if _upsert_row(db, instrument, as_of, frame.iloc[-1]):
            updated += 1

    db.commit()
    return {"instruments": len(instruments), "updated": updated, "status": "ok"}
