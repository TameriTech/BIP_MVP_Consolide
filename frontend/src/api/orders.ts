import { http } from "./http";
import type { Execution, Order, OrderSide, OrderStatus, OrderType } from "./types";

export const ordersApi = {
  submit: (data: { instrument_id: string; side: OrderSide; order_type: OrderType; quantity: string; limit_price?: string }) =>
    http.post<Order>("/orders", data).then((r) => r.data),

  list: (params?: { status_filter?: OrderStatus; instrument_id?: string }) =>
    http.get<Order[]>("/orders", { params }).then((r) => r.data),

  get: (id: string) => http.get<Order>(`/orders/${id}`).then((r) => r.data),

  cancel: (id: string) => http.post<Order>(`/orders/${id}/cancel`).then((r) => r.data),

  executions: (id: string) => http.get<Execution[]>(`/orders/${id}/executions`).then((r) => r.data),

  listAllBackoffice: (params?: { status_filter?: OrderStatus; account_id?: string }) =>
    http.get<Order[]>("/backoffice/orders", { params }).then((r) => r.data),

  listAllExecutionsBackoffice: () => http.get<Execution[]>("/backoffice/executions").then((r) => r.data),
};
