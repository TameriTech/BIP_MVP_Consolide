<script setup lang="ts">
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dropdown from "primevue/dropdown";
import Tag from "primevue/tag";
import { onMounted, ref, watch } from "vue";

import { ordersApi } from "@/api/orders";
import type { Order, OrderStatus } from "@/api/types";

const orders = ref<Order[]>([]);
const loading = ref(true);
const statusFilter = ref<OrderStatus | null>(null);
const statusOptions = [
  { label: "All", value: null },
  { label: "Executed", value: "executed" },
  { label: "Rejected", value: "rejected" },
  { label: "Cancelled", value: "cancelled" },
  { label: "Reserved", value: "reserved" },
];

const statusSeverity: Record<string, string> = {
  executed: "success",
  rejected: "danger",
  cancelled: "secondary",
  reserved: "info",
  submitted: "info",
};

async function load() {
  loading.value = true;
  try {
    orders.value = await ordersApi.listAllBackoffice(statusFilter.value ? { status_filter: statusFilter.value } : undefined);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(statusFilter, load);
</script>

<template>
  <div class="page">
    <div class="header">
      <h1>All orders</h1>
      <Dropdown v-model="statusFilter" :options="statusOptions" option-label="label" option-value="value" class="filter" />
    </div>

    <DataTable :value="orders" :loading="loading" striped-rows>
      <Column field="created_at" header="Date">
        <template #body="{ data }">{{ new Date(data.created_at).toLocaleString() }}</template>
      </Column>
      <Column field="account_id" header="Account" />
      <Column field="side" header="Side" />
      <Column field="order_type" header="Type" />
      <Column field="quantity" header="Qty" />
      <Column field="status" header="Status">
        <template #body="{ data }"><Tag :value="data.status" :severity="statusSeverity[data.status] ?? 'secondary'" /></template>
      </Column>
      <Column field="rejection_reason" header="Reason" />
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
}
.filter {
  min-width: 200px;
}
</style>
