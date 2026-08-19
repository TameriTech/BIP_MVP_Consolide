import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.services import market_data_service

logger = logging.getLogger("app.workers.quote_refresh")

_scheduler: BackgroundScheduler | None = None


def run_backfill_once() -> None:
    db = SessionLocal()
    try:
        result = market_data_service.backfill_history(db)
        logger.info("startup market backfill: %s", result)
    except Exception:
        logger.warning("startup market backfill failed", exc_info=True)
    finally:
        db.close()


def _refresh_job() -> None:
    db = SessionLocal()
    try:
        result = market_data_service.refresh_latest(db)
        logger.info("periodic market refresh: %s", result)
    except Exception:
        logger.warning("periodic market refresh failed", exc_info=True)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _refresh_job,
        "interval",
        minutes=settings.quote_refresh_interval_minutes,
        id="quote_refresh",
        next_run_time=None,  # first run scheduled by the interval, not immediately (startup backfill covers that)
    )
    _scheduler.start()
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
