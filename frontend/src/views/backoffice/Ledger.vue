<script setup lang="ts">
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Tag from "primevue/tag";
import { onMounted, ref } from "vue";

import { ledgerApi } from "@/api/ledger";
import type { LedgerEntry } from "@/api/types";

const entries = ref<LedgerEntry[]>([]);
const loading = ref(true);

onMounted(async () => {
  loading.value = true;
  try {
    entries.value = await ledgerApi.getAllBackoffice();
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page">
    <h1>All ledger entries</h1>
    <DataTable :value="entries" :loading="loading" striped-rows paginator :rows="25">
      <Column field="created_at" header="Date">
        <template #body="{ data }">{{ new Date(data.created_at).toLocaleString() }}</template>
      </Column>
      <Column field="account_id" header="Account" />
      <Column field="entry_type" header="Type">
        <template #body="{ data }"><Tag :value="data.entry_type" /></template>
      </Column>
      <Column field="amount" header="Amount">
        <template #body="{ data }">
          <span :class="Number(data.amount) < 0 ? 'neg' : 'pos'">{{ data.amount }} {{ data.currency }}</span>
        </template>
      </Column>
      <Column field="balance_after" header="Balance after">
        <template #body="{ data }">{{ data.balance_after }} {{ data.currency }}</template>
      </Column>
      <Column field="reference" header="Reference" />
    </DataTable>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.pos {
  color: var(--bip-green);
  font-weight: 600;
}
.neg {
  color: var(--bip-red);
  font-weight: 600;
}
</style>
