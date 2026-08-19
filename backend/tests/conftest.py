import os

# Must be set before any `app.*` module is imported: app.core.config.Settings is
# instantiated once at import time, and this flag stops the FastAPI lifespan from
# spawning real background yfinance/APScheduler jobs during tests (see app/main.py).
os.environ.setdefault("TESTING", "true")

import psycopg2
import pytest
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

# Tests run against a dedicated *_test database on the same Postgres server —
# never the dev database, since the schema fixture below drops all tables at
# session end (dropping dev's seeded data would be a nasty surprise).
_dev_url = make_url(settings.database_url)
_test_url = _dev_url.set(database=f"{_dev_url.database}_test")

engine = create_engine(_test_url)


def _ensure_test_database_exists() -> None:
    conn = psycopg2.connect(
        dbname="postgres",
        user=_dev_url.username,
        password=_dev_url.password,
        host=_dev_url.host,
        port=_dev_url.port,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (_test_url.database,))
            if cur.fetchone() is None:
                cur.execute(f'CREATE DATABASE "{_test_url.database}"')
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    _ensure_test_database_exists()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Session:
    """A DB session bound to an outer transaction that is always rolled back.

    Code under test is free to call db.commit()/db.rollback() (needed since
    engine code uses `with db.begin(): ...`) — a SAVEPOINT is restarted after
    each inner transaction ends so the outer rollback at teardown still undoes
    everything the test wrote.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    from fastapi.testclient import TestClient

    from app.db.session import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
