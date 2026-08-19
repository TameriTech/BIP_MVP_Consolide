<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dropdown from "primevue/dropdown";
import Tag from "primevue/tag";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";

import { adminApi } from "@/api/admin";
import { errorMessage } from "@/api/http";
import type { AccountAdmin, AccountStatus, Role, User } from "@/api/types";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const toast = useToast();

const users = ref<User[]>([]);
const accounts = ref<AccountAdmin[]>([]);
const loading = ref(true);
const savingUserId = ref<string | null>(null);
const savingAccountId = ref<string | null>(null);

const roleOptions: Role[] = ["investor", "admin", "backoffice_operator", "super_admin"];
const statusOptions: AccountStatus[] = ["pending", "active", "suspended", "closed"];

async function load() {
  loading.value = true;
  try {
    [users.value, accounts.value] = await Promise.all([adminApi.listUsers(), adminApi.listAccounts()]);
  } finally {
    loading.value = false;
  }
}

onMounted(load);

async function changeRole(user: User, role: Role) {
  if (role === user.role) return;
  savingUserId.value = user.id;
  try {
    const updated = await adminApi.updateUserRole(user.id, role);
    const idx = users.value.findIndex((u) => u.id === user.id);
    if (idx !== -1) users.value[idx] = updated;
    toast.add({ severity: "success", summary: "Role updated", life: 2000 });
  } catch (e) {
    toast.add({ severity: "error", summary: "Failed", detail: errorMessage(e), life: 5000 });
  } finally {
    savingUserId.value = null;
  }
}

async function changeStatus(account: AccountAdmin, status: AccountStatus) {
  if (status === account.status) return;
  savingAccountId.value = account.id;
  try {
    const updated = await adminApi.updateAccountStatus(account.id, status);
    const idx = accounts.value.findIndex((a) => a.id === account.id);
    if (idx !== -1) accounts.value[idx] = updated;
    toast.add({ severity: "success", summary: "Account status updated", life: 2000 });
  } catch (e) {
    toast.add({ severity: "error", summary: "Failed", detail: errorMessage(e), life: 5000 });
  } finally {
    savingAccountId.value = null;
  }
}

function emailFor(userId: string) {
  return users.value.find((u) => u.id === userId)?.email ?? userId;
}
</script>

<template>
  <div class="page">
    <h1>Users &amp; accounts</h1>

    <Card>
      <template #title>Users</template>
      <template #content>
        <DataTable :value="users" :loading="loading" striped-rows>
          <Column field="email" header="Email" />
          <Column field="full_name" header="Name" />
          <Column field="role" header="Role">
            <template #body="{ data }">
              <Dropdown
                v-if="auth.isSuperAdmin"
                :model-value="data.role"
                :options="roleOptions"
                :loading="savingUserId === data.id"
                @update:model-value="(v) => changeRole(data, v)"
              />
              <Tag
                v-else
                :value="data.role.replace('_', ' ').toUpperCase()"
                :severity="
                  data.role === 'super_admin' ? 'danger' :
                  data.role === 'admin' ? 'info' :
                  data.role === 'backoffice_operator' ? 'warn' : 'secondary'
                "
              />
            </template>
          </Column>
        </DataTable>
        <p v-if="!auth.isSuperAdmin" class="hint">Only super-admins can change user roles.</p>
      </template>
    </Card>

    <Card>
      <template #title>Accounts</template>
      <template #content>
        <DataTable :value="accounts" :loading="loading" striped-rows>
          <Column header="User">
            <template #body="{ data }">{{ emailFor(data.user_id) }}</template>
          </Column>
          <Column field="cash_balance" header="Cash balance">
            <template #body="{ data }">${{ data.cash_balance }}</template>
          </Column>
          <Column field="cash_reserved" header="Reserved">
            <template #body="{ data }">${{ data.cash_reserved }}</template>
          </Column>
          <Column field="status" header="Status">
            <template #body="{ data }">
              <Dropdown
                :model-value="data.status"
                :options="statusOptions"
                :loading="savingAccountId === data.id"
                @update:model-value="(v) => changeStatus(data, v)"
              />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.hint {
  color: var(--text-muted);
  font-size: 0.85rem;
}
</style>
