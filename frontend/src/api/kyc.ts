import { http } from "./http";
import type { KycFile, KycStatus } from "./types";

export const kycApi = {
  getMine: () => http.get<KycFile>("/kyc/me").then((r) => r.data),

  upsertMine: (data: Partial<KycFile>) => http.post<KycFile>("/kyc/me", data).then((r) => r.data),

  submitMine: () => http.post<KycFile>("/kyc/me/submit").then((r) => r.data),

  list: (status?: KycStatus) =>
    http.get<KycFile[]>("/backoffice/kyc", { params: status ? { status_filter: status } : {} }).then((r) => r.data),

  get: (id: string) => http.get<KycFile>(`/backoffice/kyc/${id}`).then((r) => r.data),

  validate: (id: string) => http.post<KycFile>(`/backoffice/kyc/${id}/validate`).then((r) => r.data),

  reject: (id: string, reason: string) =>
    http.post<KycFile>(`/backoffice/kyc/${id}/reject`, { reason }).then((r) => r.data),
};
