<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Textarea from "primevue/textarea";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";

import { adminApi } from "@/api/admin";
import { errorMessage } from "@/api/http";
import type { PlatformSetting } from "@/api/types";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const toast = useToast();

const settings = ref<PlatformSetting[]>([]);
const loading = ref(true);

const key = ref("");
const valueJson = ref("{}");
const saving = ref(false);
const error = ref("");

async function load() {
  loading.value = true;
  try {
    settings.value = await adminApi.getSettings();
  } finally {
    loading.value = false;
  }
}

onMounted(load);

async function save() {
  error.value = "";
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(valueJson.value);
  } catch {
    error.value = "Value must be valid JSON, e.g. {\"bps\": 10}";
    return;
  }
  saving.value = true;
  try {
    await adminApi.updateSetting(key.value, parsed);
    toast.add({ severity: "success", summary: "Setting saved", life: 2500 });
    key.value = "";
    valueJson.value = "{}";
    await load();
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="page">
    <h1>Platform settings</h1>

    <DataTable :value="settings" :loading="loading" striped-rows>
      <Column field="key" header="Key" />
      <Column header="Value">
        <template #body="{ data }">{{ JSON.stringify(data.value) }}</template>
      </Column>
      <Column field="updated_at" header="Updated">
        <template #body="{ data }">{{ new Date(data.updated_at).toLocaleString() }}</template>
      </Column>
    </DataTable>

    <Card v-if="auth.isSuperAdmin">
      <template #title>Add / update a setting</template>
      <template #content>
        <form class="form" @submit.prevent="save">
          <label>
            Key
            <InputText v-model="key" placeholder="fee_rate_bps" required fluid />
          </label>
          <label>
            Value (JSON)
            <Textarea v-model="valueJson" rows="3" fluid />
          </label>
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
          <Button type="submit" label="Save" :loading="saving" />
        </form>
      </template>
    </Card>
    <p v-else class="hint">Only super-admins can edit settings.</p>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 360px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
  font-size: 0.9rem;
}
.hint {
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
}
</style>
