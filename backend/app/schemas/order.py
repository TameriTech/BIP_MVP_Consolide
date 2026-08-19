import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.enums import OrderSide, OrderStatus, OrderType


class OrderCreateRequest(BaseModel):
    instrument_id: uuid.UUID
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(gt=0)
    limit_price: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _limit_price_required_for_limit_orders(self):
        if self.order_type == OrderType.limit and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        return self


class OrderOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    instrument_id: uuid.UUID
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    limit_price: Decimal | None
    estimated_amount: Decimal | None
    estimated_fees: Decimal | None
    status: OrderStatus
    rejection_reason: str | None
    created_at: datetime
    submitted_at: datetime | None
    executed_at: datetime | None
    cancelled_at: datetime | None

    model_config = {"from_attributes": True}


class ExecutionOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    instrument_id: uuid.UUID
    quantity: Decimal
    price: Decimal
    fees: Decimal
    gross_amount: Decimal
    net_amount: Decimal
    executed_at: datetime

    model_config = {"from_attributes": True}
