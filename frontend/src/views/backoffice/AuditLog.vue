<script setup lang="ts">
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputText from "primevue/inputtext";
import { onMounted, ref, watch } from "vue";

import { adminApi } from "@/api/admin";
import type { AuditEvent } from "@/api/types";

const events = ref<AuditEvent[]>([]);
const loading = ref(true);
const actionFilter = ref("");

async function load() {
  loading.value = true;
  try {
    events.value = await adminApi.listAuditLog(actionFilter.value ? { action: actionFilter.value } : undefined);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(actionFilter, load);
</script>

<template>
  <div class="page">
    <div class="header">
      <h1>Audit log</h1>
      <InputText v-model="actionFilter" placeholder="Filter by action (e.g. order.executed)" class="filter" />
    </div>

    <DataTable :value="events" :loading="loading" striped-rows paginator :rows="25">
      <Column field="created_at" header="Time">
        <template #body="{ data }">{{ new Date(data.created_at).toLocaleString() }}</template>
      </Column>
      <Column field="actor_role" header="Actor role" />
      <Column field="action" header="Action" />
      <Column field="entity_type" header="Entity" />
      <Column field="entity_id" header="Entity ID" />
      <Column header="Metadata">
        <template #body="{ data }">{{ data.event_metadata ? JSON.stringify(data.event_metadata) : "" }}</template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.filter {
  min-width: 280px;
}
</style>
