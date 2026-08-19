import { http } from "./http";
import type { Instrument, Quote } from "./types";

export const marketApi = {
  list: (params?: { market?: string; sector?: string; tradable?: boolean }) =>
    http.get<Instrument[]>("/instruments", { params }).then((r) => r.data),

  get: (symbol: string) => http.get<Instrument>(`/instruments/${symbol}`).then((r) => r.data),

  latestQuote: (symbol: string) => http.get<Quote | null>(`/instruments/${symbol}/quote`).then((r) => r.data),

  quotes: (symbol: string) => http.get<Quote[]>(`/instruments/${symbol}/quotes`).then((r) => r.data),

  createInstrument: (data: { symbol: string; name: string; market?: string; sector?: string; currency?: string }) =>
    http.post<Instrument>("/backoffice/instruments", data).then((r) => r.data),

  updateInstrument: (id: string, data: Partial<{ name: string; sector: string; tradable: boolean }>) =>
    http.patch<Instrument>(`/backoffice/instruments/${id}`, data).then((r) => r.data),

  refresh: () => http.post("/backoffice/market/refresh").then((r) => r.data),
};
