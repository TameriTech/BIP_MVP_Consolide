import axios from "axios";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8010/api/v1",
});

function getTokens() {
  return {
    access: localStorage.getItem("bip_access_token"),
    refresh: localStorage.getItem("bip_refresh_token"),
  };
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("bip_access_token", access);
  localStorage.setItem("bip_refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("bip_access_token");
  localStorage.removeItem("bip_refresh_token");
}

http.interceptors.request.use((config) => {
  const { access } = getTokens();
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const { refresh } = getTokens();
  if (!refresh) throw new Error("no refresh token");
  const { data } = await axios.post(`${http.defaults.baseURL}/auth/refresh`, { refresh_token: refresh });
  setTokens(data.access_token, data.refresh_token);
  return data.access_token;
}

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && localStorage.getItem("bip_refresh_token")) {
      original._retry = true;
      try {
        refreshPromise = refreshPromise ?? refreshAccessToken();
        const token = await refreshPromise;
        refreshPromise = null;
        original.headers.Authorization = `Bearer ${token}`;
        return http(original);
      } catch (refreshError) {
        refreshPromise = null;
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  },
);

export interface ApiError {
  error: { code: string; message: string; details?: Record<string, unknown> };
}

export function errorMessage(err: unknown): string {
  const data = (err as any)?.response?.data as ApiError | undefined;
  return data?.error?.message ?? "Something went wrong. Please try again.";
}
