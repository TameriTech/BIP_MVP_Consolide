"""Shared helper for taking a `SELECT ... FOR UPDATE` row lock.

Critical detail: `populate_existing=True` is mandatory here. Every request
that reaches the order engine has already loaded the caller's Account once,
unlocked, earlier in the same session (e.g. `account_service.get_account_for_user`).
SQLAlchemy's identity map means a second SELECT for the same primary key
normally returns that SAME Python object *without* refreshing its attributes
from the new row — so the lock would be correctly acquired at the DB level,
but the in-memory `cash_reserved`/`cash_balance` a caller then reads back
would still be the stale pre-lock snapshot. That silently defeats the whole
reservation mechanism: a second concurrent request would see yesterday's
numbers and think funds/shares are available when they no longer are.
`populate_existing=True` forces the freshly-locked row's data to overwrite
the cached object, which is what makes concurrent requests actually see each
other's committed changes once they acquire the lock.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session


def lock_row(db: Session, model, row_id: uuid.UUID):
    return db.execute(
        select(model).where(model.id == row_id).with_for_update().execution_options(populate_existing=True)
    ).scalar_one()
