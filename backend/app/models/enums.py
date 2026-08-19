import enum


class RoleEnum(str, enum.Enum):
    investor = "investor"
    admin = "admin"
    backoffice_operator = "backoffice_operator"
    super_admin = "super_admin"


class AccountStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"
    closed = "closed"


class KycStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    validated = "validated"
    rejected = "rejected"


class OrderSide(str, enum.Enum):
    buy = "buy"
    sell = "sell"


class OrderType(str, enum.Enum):
    market = "market"
    limit = "limit"


class OrderStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    reserved = "reserved"
    executed = "executed"
    cancelled = "cancelled"
    rejected = "rejected"


class ReservationKind(str, enum.Enum):
    cash = "cash"
    shares = "shares"


class ReservationStatus(str, enum.Enum):
    active = "active"
    released = "released"
    consumed = "consumed"


class LedgerEntryType(str, enum.Enum):
    initial_credit = "initial_credit"
    trade_buy = "trade_buy"
    trade_sell = "trade_sell"
    fee = "fee"
