from datetime import datetime, timezone

import pandas as pd
import pytest

from app.models.instrument import Instrument
from app.models.quote import Quote
from app.services import market_data_service


@pytest.fixture()
def one_instrument(db):
    instrument = Instrument(symbol="AAPL", name="Apple Inc.", market="DEMO", currency="USD", tradable=True)
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


@pytest.fixture()
def two_instruments(db):
    a = Instrument(symbol="AAPL", name="Apple Inc.", market="DEMO", currency="USD", tradable=True)
    b = Instrument(symbol="MSFT", name="Microsoft Corp.", market="DEMO", currency="USD", tradable=True)
    db.add_all([a, b])
    db.commit()
    db.refresh(a)
    db.refresh(b)
    return a, b


def _flat_frame():
    idx = pd.date_range("2026-01-01", periods=3, freq="D", tz="UTC")
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [105.0, 106.0, 107.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [104.0, 105.5, 106.75],
            "Volume": [1000, 1100, 1200],
        },
        index=idx,
    )


def _multiindex_frame(symbols: list[str]):
    idx = pd.date_range("2026-01-01", periods=2, freq="D", tz="UTC")
    frames = {}
    for i, symbol in enumerate(symbols):
        frames[symbol] = pd.DataFrame(
            {
                "Open": [10.0 + i, 11.0 + i],
                "High": [12.0 + i, 13.0 + i],
                "Low": [9.0 + i, 10.0 + i],
                "Close": [11.5 + i, 12.5 + i],
                "Volume": [500 + i, 600 + i],
            },
            index=idx,
        )
    return pd.concat(frames, axis=1)


def test_backfill_single_instrument_upserts_quotes(monkeypatch, db, one_instrument):
    monkeypatch.setattr(market_data_service, "_download", lambda symbols, period, interval: _flat_frame())

    result = market_data_service.backfill_history(db)

    assert result["status"] == "ok"
    assert result["quotes_upserted"] == 3
    quotes = db.query(Quote).filter(Quote.instrument_id == one_instrument.id).all()
    assert len(quotes) == 3
    db.refresh(one_instrument)
    assert one_instrument.last_price == quotes[-1].price


def test_backfill_multi_instrument_multiindex(monkeypatch, db, two_instruments):
    a, b = two_instruments
    monkeypatch.setattr(
        market_data_service, "_download", lambda symbols, period, interval: _multiindex_frame(["AAPL", "MSFT"])
    )

    result = market_data_service.backfill_history(db)

    assert result["status"] == "ok"
    assert result["quotes_upserted"] == 4
    assert db.query(Quote).filter(Quote.instrument_id == a.id).count() == 2
    assert db.query(Quote).filter(Quote.instrument_id == b.id).count() == 2


def test_backfill_is_idempotent(monkeypatch, db, one_instrument):
    monkeypatch.setattr(market_data_service, "_download", lambda symbols, period, interval: _flat_frame())

    market_data_service.backfill_history(db)
    result = market_data_service.backfill_history(db)

    assert result["quotes_upserted"] == 0  # already-seen (instrument_id, as_of) pairs are skipped
    assert db.query(Quote).filter(Quote.instrument_id == one_instrument.id).count() == 3


def test_backfill_handles_yfinance_failure_gracefully(monkeypatch, db, one_instrument):
    monkeypatch.setattr(market_data_service, "_download", lambda symbols, period, interval: None)

    result = market_data_service.backfill_history(db)

    assert result["status"] == "yfinance_unavailable"
    assert result["quotes_upserted"] == 0
    assert db.query(Quote).count() == 0


def test_refresh_latest_updates_last_price(monkeypatch, db, one_instrument):
    monkeypatch.setattr(market_data_service, "_download", lambda symbols, period, interval: _flat_frame())

    result = market_data_service.refresh_latest(db)

    assert result["status"] == "ok"
    assert result["updated"] == 1
    db.refresh(one_instrument)
    assert one_instrument.last_price == pytest.approx(106.75)
    assert one_instrument.last_price_at is not None


def test_ignores_nan_close_rows():
    import math

    idx = pd.date_range("2026-01-01", periods=1, tz="UTC")
    frame = pd.DataFrame({"Open": [1.0], "High": [1.0], "Low": [1.0], "Close": [math.nan], "Volume": [1]}, index=idx)
    row = frame.iloc[0]
    assert market_data_service._to_decimal(row["Close"]) is None
