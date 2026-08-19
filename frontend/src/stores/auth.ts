import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { authApi } from "@/api/auth";
import { clearTokens, setTokens } from "@/api/http";
import type { User } from "@/api/types";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const initialized = ref(false);

  const isAuthenticated = computed(() => user.value !== null);
  const isStaff = computed(
    () => user.value !== null && ["admin", "backoffice_operator", "super_admin"].includes(user.value.role),
  );
  const isSuperAdmin = computed(() => user.value?.role === "super_admin");

  async function fetchMe() {
    try {
      user.value = await authApi.me();
    } catch {
      user.value = null;
    } finally {
      initialized.value = true;
    }
  }

  async function login(email: string, password: string) {
    const tokens = await authApi.login({ email, password });
    setTokens(tokens.access_token, tokens.refresh_token);
    await fetchMe();
  }

  async function register(data: { email: string; password: string; full_name: string; phone?: string }) {
    const tokens = await authApi.register(data);
    setTokens(tokens.access_token, tokens.refresh_token);
    await fetchMe();
  }

  function logout() {
    clearTokens();
    user.value = null;
    authApi.logout().catch(() => undefined);
  }

  return { user, initialized, isAuthenticated, isStaff, isSuperAdmin, fetchMe, login, register, logout };
});
