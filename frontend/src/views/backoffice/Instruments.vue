<script setup lang="ts">
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import ToggleSwitch from "primevue/toggleswitch";
import { useToast } from "primevue/usetoast";
import { onMounted, reactive, ref } from "vue";

import { errorMessage } from "@/api/http";
import { marketApi } from "@/api/market";
import type { Instrument } from "@/api/types";

const toast = useToast();
const instruments = ref<Instrument[]>([]);
const loading = ref(true);
const saving = ref<string | null>(null);
const refreshing = ref(false);

const createVisible = ref(false);
const createForm = reactive({ symbol: "", name: "", sector: "" });
const createError = ref("");
const creating = ref(false);

async function load() {
  loading.value = true;
  try {
    instruments.value = await marketApi.list();
  } finally {
    loading.value = false;
  }
}

onMounted(load);

async function toggleTradable(instrument: Instrument, value: boolean) {
  saving.value = instrument.id;
  try {
    const updated = await marketApi.updateInstrument(instrument.id, { tradable: value });
    const idx = instruments.value.findIndex((i) => i.id === instrument.id);
    if (idx !== -1) instruments.value[idx] = updated;
  } catch (e) {
    toast.add({ severity: "error", summary: "Failed", detail: errorMessage(e), life: 5000 });
  } finally {
    saving.value = null;
  }
}

async function createInstrument() {
  creating.value = true;
  createError.value = "";
  try {
    await marketApi.createInstrument({ symbol: createForm.symbol, name: createForm.name, sector: createForm.sector || undefined });
    createVisible.value = false;
    createForm.symbol = "";
    createForm.name = "";
    createForm.sector = "";
    toast.add({ severity: "success", summary: "Instrument created", life: 2500 });
    await load();
  } catch (e) {
    createError.value = errorMessage(e);
  } finally {
    creating.value = false;
  }
}

async function refreshMarket() {
  refreshing.value = true;
  try {
    const result: any = await marketApi.refresh();
    toast.add({
      severity: result.status === "ok" ? "success" : "warn",
      summary: "Market refresh",
      detail: result.status === "ok" ? `${result.updated} instrument(s) updated.` : "yfinance unavailable — using existing prices.",
      life: 4000,
    });
    await load();
  } finally {
    refreshing.value = false;
  }
}
</script>

<template>
  <div class="page">
    <div class="header">
      <h1>Instruments</h1>
      <div class="actions">
        <Button label="Refresh prices" severity="secondary" :loading="refreshing" @click="refreshMarket" />
        <Button label="Add instrument" @click="createVisible = true" />
      </div>
    </div>

    <DataTable :value="instruments" :loading="loading" striped-rows>
      <Column field="symbol" header="Symbol" />
      <Column field="name" header="Name" />
      <Column field="sector" header="Sector" />
      <Column field="last_price" header="Last price">
        <template #body="{ data }">${{ data.last_price ?? "—" }}</template>
      </Column>
      <Column field="last_price_at" header="As of">
        <template #body="{ data }">{{ data.last_price_at ? new Date(data.last_price_at).toLocaleString() : "—" }}</template>
      </Column>
      <Column header="Tradable">
        <template #body="{ data }">
          <ToggleSwitch
            :model-value="data.tradable"
            :disabled="saving === data.id"
            @update:model-value="(v) => toggleTradable(data, v)"
          />
        </template>
      </Column>
    </DataTable>

    <Dialog v-model:visible="createVisible" header="Add instrument" modal :style="{ width: '360px' }">
      <form class="form" @submit.prevent="createInstrument">
        <label>
          Symbol
          <InputText v-model="createForm.symbol" required fluid />
        </label>
        <label>
          Name
          <InputText v-model="createForm.name" required fluid />
        </label>
        <label>
          Sector
          <InputText v-model="createForm.sector" fluid />
        </label>
        <Message v-if="createError" severity="error" :closable="false">{{ createError }}</Message>
      </form>
      <template #footer>
        <Button label="Cancel" severity="secondary" @click="createVisible = false" />
        <Button label="Create" :loading="creating" @click="createInstrument" />
      </template>
    </Dialog>
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
.actions {
  display: flex;
  gap: 0.75rem;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
  font-size: 0.9rem;
}
</style>
