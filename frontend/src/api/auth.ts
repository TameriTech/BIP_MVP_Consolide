import { http } from "./http";
import type { TokenPair, User } from "./types";

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; phone?: string }) =>
    http.post<TokenPair>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    http.post<TokenPair>("/auth/login", data).then((r) => r.data),

  me: () => http.get<User>("/auth/me").then((r) => r.data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    http.post("/auth/change-password", data),

  logout: () => http.post("/auth/logout"),
};
