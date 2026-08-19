import { http } from "./http";
import type { AccountAdmin, AccountStatus, AuditEvent, PlatformSetting, Role, User } from "./types";

export const adminApi = {
  listUsers: () => http.get<User[]>("/backoffice/users").then((r) => r.data),
  getUser: (id: string) => http.get<User>(`/backoffice/users/${id}`).then((r) => r.data),
  updateUserRole: (id: string, role: Role) =>
    http.patch<User>(`/backoffice/users/${id}/role`, { role }).then((r) => r.data),

  listAccounts: (status?: AccountStatus) =>
    http.get<AccountAdmin[]>("/backoffice/accounts", { params: status ? { status_filter: status } : {} }).then((r) => r.data),
  updateAccountStatus: (id: string, status: AccountStatus) =>
    http.patch<AccountAdmin>(`/backoffice/accounts/${id}/status`, { status }).then((r) => r.data),

  listAuditLog: (params?: { actor_user_id?: string; entity_type?: string; action?: string }) =>
    http.get<AuditEvent[]>("/backoffice/audit-log", { params }).then((r) => r.data),

  getSettings: () => http.get<PlatformSetting[]>("/backoffice/settings").then((r) => r.data),
  updateSetting: (key: string, value: Record<string, unknown>) =>
    http.patch<PlatformSetting>(`/backoffice/settings/${key}`, { value }).then((r) => r.data),
};
