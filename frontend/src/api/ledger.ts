import { http } from "./http";
import type { LedgerEntry, LedgerEntryType } from "./types";

export const ledgerApi = {
  getMine: (params?: { entry_type?: LedgerEntryType; date_from?: string; date_to?: string }) =>
    http.get<LedgerEntry[]>("/ledger/me", { params }).then((r) => r.data),

  getAllBackoffice: (params?: { account_id?: string; entry_type?: LedgerEntryType }) =>
    http.get<LedgerEntry[]>("/backoffice/ledger", { params }).then((r) => r.data),
};
