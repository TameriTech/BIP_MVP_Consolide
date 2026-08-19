"""Order Management System — the single place order.status is ever mutated.

Every status change in the codebase must go through `transition()`. Never
assign `order.status = ...` anywhere else.
"""

from datetime import datetime, timezone

from app.core.errors import InvalidOrderStateError
from app.models.enums import OrderStatus
from app.models.order import Order

ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.draft: {OrderStatus.submitted},
    OrderStatus.submitted: {OrderStatus.reserved, OrderStatus.rejected},
    OrderStatus.reserved: {OrderStatus.executed, OrderStatus.rejected, OrderStatus.cancelled},
    OrderStatus.executed: set(),
    OrderStatus.cancelled: set(),
    OrderStatus.rejected: set(),
}


def transition(order: Order, to_status: OrderStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(order.status, set())
    if to_status not in allowed:
        raise InvalidOrderStateError(
            f"cannot transition order from {order.status.value} to {to_status.value}",
            {"from": order.status.value, "to": to_status.value},
        )
    order.status = to_status
    now = datetime.now(timezone.utc)
    if to_status == OrderStatus.executed:
        order.executed_at = now
    elif to_status == OrderStatus.cancelled:
        order.cancelled_at = now
