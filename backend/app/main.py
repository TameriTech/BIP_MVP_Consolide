from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import threading

from app.core.config import settings
from app.core.errors import AppError, app_error_handler
from app.routers import auth, backoffice, health, kyc, ledger, market, orders, portfolio
from app.workers.quote_refresh import run_backfill_once, start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Backgrounded: yfinance can be slow (retries/backoff on rate limiting),
    # and must never delay the app from accepting requests / passing health checks.
    # Skipped entirely under pytest — tests drive market_data_service directly
    # (mocking its network call) and must never trigger real yfinance traffic
    # just because a TestClient's lifespan happened to start.
    if not settings.testing:
        threading.Thread(target=run_backfill_once, daemon=True).start()
        start_scheduler()
    yield
    if not settings.testing:
        stop_scheduler()


app = FastAPI(title="BIP API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(kyc.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(ledger.router, prefix="/api/v1")
app.include_router(backoffice.router, prefix="/api/v1")
