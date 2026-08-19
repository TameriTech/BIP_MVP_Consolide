<script setup lang="ts">
import Button from "primevue/button";
import Message from "primevue/message";
import Password from "primevue/password";
import { useToast } from "primevue/usetoast";
import { ref } from "vue";

import { authApi } from "@/api/auth";
import { errorMessage } from "@/api/http";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const toast = useToast();

const roleLabel: Record<string, string> = {
  investor: "Investor",
  admin: "Admin",
  backoffice_operator: "Back-office Operator",
  super_admin: "Super Admin",
};

const currentPassword = ref("");
const newPassword = ref("");
const loading = ref(false);
const error = ref("");

async function changePassword() {
  loading.value = true;
  error.value = "";
  try {
    await authApi.changePassword({ current_password: currentPassword.value, new_password: newPassword.value });
    toast.add({ severity: "success", summary: "Password changed", life: 2500 });
    currentPassword.value = "";
    newPassword.value = "";
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page animate-fade-in">
    <h1>Account settings</h1>

    <div class="panel">
      <div class="panel-header"><h2>Profile</h2></div>
      <div class="panel-body">
        <div class="profile-row">
          <div class="avatar">{{ (auth.user?.full_name ?? "").split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() }}</div>
          <div>
            <div class="profile-name">{{ auth.user?.full_name }}</div>
            <div class="profile-email">{{ auth.user?.email }}</div>
          </div>
          <span class="role-tag">{{ roleLabel[auth.user?.role ?? ""] ?? auth.user?.role }}</span>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header"><h2>Change password</h2></div>
      <div class="panel-body">
        <form class="form" @submit.prevent="changePassword">
          <div class="field">
            <label>Current password</label>
            <Password v-model="currentPassword" :feedback="false" toggle-mask required fluid />
          </div>
          <div class="field">
            <label>New password</label>
            <Password v-model="newPassword" toggle-mask required fluid />
          </div>
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
          <Button type="submit" label="Update password" :loading="loading" />
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 520px;
}
.panel {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.panel-header { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--surface-border); }
.panel-header h2 {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--text-secondary);
  margin: 0;
}
.panel-body { padding: 1.5rem; }

.profile-row { display: flex; align-items: center; gap: 1rem; }
.avatar {
  width: 46px; height: 46px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-sm); font-weight: 800; color: white;
  flex-shrink: 0;
}
.profile-name { font-size: var(--text-md); font-weight: 700; color: var(--text-primary); }
.profile-email { font-size: var(--text-sm); color: var(--text-muted); margin-top: 1px; }
.role-tag {
  margin-left: auto;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--bip-gold);
  background: rgba(240,180,41,0.1);
  border: 1px solid rgba(240,180,41,0.25);
  border-radius: 99px;
  padding: 0.3rem 0.75rem;
  flex-shrink: 0;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.field label {
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
</style>
