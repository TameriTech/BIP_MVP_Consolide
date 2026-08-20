export type Role = "investor" | "admin" | "backoffice_operator" | "super_admin";
export type AccountStatus = "pending" | "active" | "suspended" | "closed";
export type KycStatus = "draft" | "submitted" | "validated" | "rejected";
export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit";
export type OrderStatus = "draft" | "submitted" | "reserved" | "executed" | "cancelled" | "rejected";
export type LedgerEntryType = "initial_credit" | "trade_buy" | "trade_sell" | "fee";

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: Role;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface KycFile {
  id: string;
  account_id: string;
  status: KycStatus;
  full_legal_name: string | null;
  birth_date: string | null;
  country: string | null;
  id_document_type: string | null;
  id_document_number: string | null;
  rejection_reason: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Instrument {
  id: string;
  symbol: string;
  name: string;
  market: string;
  sector: string | null;
  currency: string;
  tradable: boolean;
  last_price: string | null;
  last_price_at: string | null;
}

export interface Quote {
  price: string;
  as_of: string;
  open: string | null;
  high: string | null;
  low: string | null;
  close: string | null;
  volume: number | null;
  source: string;
}

export interface Order {
  id: string;
  account_id: string;
  instrument_id: string;
  side: OrderSide;
  order_type: OrderType;
  quantity: string;
  limit_price: string | null;
  estimated_amount: string | null;
  estimated_fees: string | null;
  status: OrderStatus;
  rejection_reason: string | null;
  created_at: string;
  submitted_at: string | null;
  executed_at: string | null;
  cancelled_at: string | null;
}

export interface Execution {
  id: string;
  order_id: string;
  instrument_id: string;
  quantity: string;
  price: string;
  fees: string;
  gross_amount: string;
  net_amount: string;
  executed_at: string;
}

export interface PositionView {
  instrument_id: string;
  symbol: string;
  quantity: string;
  reserved_quantity: string;
  avg_cost: string;
  last_price: string | null;
  market_value: string;
}

export interface Portfolio {
  currency: string;
  cash_balance: string;
  cash_reserved: string;
  cash_available: string;
  positions_value: string;
  total_value: string;
  positions: PositionView[];
}

export interface Performance {
  total_value: string;
  cost_basis: string;
  unrealized_pl: string;
  unrealized_pl_pct: string;
}

export interface LedgerEntry {
  id: number;
  reference: string;
  account_id: string;
  entry_type: LedgerEntryType;
  amount: string;
  currency: string;
  balance_after: string;
  order_id: string | null;
  execution_id: string | null;
  instrument_id: string | null;
  created_at: string;
  note: string | null;
}

export interface AccountAdmin {
  id: string;
  user_id: string;
  status: AccountStatus;
  currency: string;
  cash_balance: string;
  cash_reserved: string;
  activated_at: string | null;
  created_at: string;
}

export interface AuditEvent {
  id: number;
  actor_user_id: string | null;
  actor_role: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  event_metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface PlatformSetting {
  key: string;
  value: Record<string, unknown>;
  updated_at: string;
}
