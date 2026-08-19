import uuid
from decimal import Decimal

import pytest

from app.core.errors import InvalidOrderStateError
from app.engine import oms
from app.models.enums import OrderSide, OrderStatus, OrderType
from app.models.order import Order


def _order(status=OrderStatus.submitted) -> Order:
    return Order(
        id=uuid.uuid4(), account_id=uuid.uuid4(), instrument_id=uuid.uuid4(),
        side=OrderSide.buy, order_type=OrderType.market, quantity=Decimal("1"), status=status,
    )


@pytest.mark.parametrize(
    "frm,to",
    [
        (OrderStatus.submitted, OrderStatus.reserved),
        (OrderStatus.submitted, OrderStatus.rejected),
        (OrderStatus.reserved, OrderStatus.executed),
        (OrderStatus.reserved, OrderStatus.rejected),
        (OrderStatus.reserved, OrderStatus.cancelled),
    ],
)
def test_allowed_transitions_succeed(frm, to):
    order = _order(frm)
    oms.transition(order, to)
    assert order.status == to


@pytest.mark.parametrize(
    "frm,to",
    [
        (OrderStatus.submitted, OrderStatus.executed),
        (OrderStatus.executed, OrderStatus.cancelled),
        (OrderStatus.rejected, OrderStatus.reserved),
        (OrderStatus.cancelled, OrderStatus.executed),
        (OrderStatus.draft, OrderStatus.reserved),
    ],
)
def test_disallowed_transitions_raise(frm, to):
    order = _order(frm)
    with pytest.raises(InvalidOrderStateError):
        oms.transition(order, to)
    assert order.status == frm  # unchanged on rejection


def test_executed_sets_executed_at():
    order = _order(OrderStatus.reserved)
    oms.transition(order, OrderStatus.executed)
    assert order.executed_at is not None


def test_cancelled_sets_cancelled_at():
    order = _order(OrderStatus.reserved)
    oms.transition(order, OrderStatus.cancelled)
    assert order.cancelled_at is not None
