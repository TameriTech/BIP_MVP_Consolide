from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.instrument import Instrument
from app.models.position import Position


def get_portfolio(db: Session, account: Account) -> dict:
    """Computed on read from Account + Positions + Instrument prices —
    deliberately NOT a stored table, so it can never drift from the ledger
    (the doc's own §14 requirement: "cohérence permanente avec le ledger").
    """
    positions = (
        db.query(Position)
        .filter(Position.account_id == account.id, Position.quantity > 0)
        .all()
    )

    position_views = []
    positions_value = Decimal("0")
    for position in positions:
        instrument = db.get(Instrument, position.instrument_id)
        market_value = (
            (position.quantity * instrument.last_price).quantize(Decimal("0.01"))
            if instrument.last_price is not None
            else Decimal("0.00")
        )
        positions_value += market_value
        position_views.append(
            {
                "instrument_id": position.instrument_id,
                "symbol": instrument.symbol,
                "quantity": position.quantity,
                "reserved_quantity": position.reserved_quantity,
                "avg_cost": position.avg_cost,
                "last_price": instrument.last_price,
                "market_value": market_value,
            }
        )

    return {
        "currency": account.currency,
        "cash_balance": account.cash_balance,
        "cash_reserved": account.cash_reserved,
        "cash_available": account.cash_balance - account.cash_reserved,
        "positions_value": positions_value,
        "total_value": account.cash_balance + positions_value,
        "positions": position_views,
    }


def get_performance(db: Session, account: Account) -> dict:
    portfolio = get_portfolio(db, account)
    cost_basis = Decimal("0")
    unrealized_pl = Decimal("0")
    for p in portfolio["positions"]:
        cost_basis += (p["avg_cost"] * p["quantity"]).quantize(Decimal("0.01"))
        if p["last_price"] is not None:
            unrealized_pl += ((p["last_price"] - p["avg_cost"]) * p["quantity"]).quantize(Decimal("0.01"))

    return {
        "total_value": portfolio["total_value"],
        "cost_basis": cost_basis,
        "unrealized_pl": unrealized_pl,
        "unrealized_pl_pct": (unrealized_pl / cost_basis * 100) if cost_basis > 0 else Decimal("0"),
    }
