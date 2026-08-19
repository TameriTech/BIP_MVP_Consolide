from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic autogenerate and Base.metadata.create_all see them.
from app.models import (  # noqa: E402,F401
    user,
    account,
    kyc,
    instrument,
    quote,
    position,
    order,
    reservation,
    execution,
    ledger,
    audit,
    settings as settings_model,
)
