<script setup lang="ts">
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import Dropdown from "primevue/dropdown";
import Tag from "primevue/tag";
import Textarea from "primevue/textarea";
import { useToast } from "primevue/usetoast";
import { onMounted, ref, watch } from "vue";

import { errorMessage } from "@/api/http";
import { kycApi } from "@/api/kyc";
import type { KycFile, KycStatus } from "@/api/types";

const toast = useToast();
const files = ref<KycFile[]>([]);
const loading = ref(true);
const statusFilter = ref<KycStatus>("submitted");
const statusOptions: { label: string; value: KycStatus }[] = [
  { label: "Submitted (pending review)", value: "submitted" },
  { label: "Validated", value: "validated" },
  { label: "Rejected", value: "rejected" },
  { label: "Draft", value: "draft" },
];

const rejectVisible = ref(false);
const rejectTarget = ref<KycFile | null>(null);
const rejectReason = ref("");
const acting = ref(false);

async function load() {
  loading.value = true;
  try {
    files.value = await kycApi.list(statusFilter.value);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(statusFilter, load);

async function validate(file: KycFile) {
  acting.value = true;
  try {
    await kycApi.validate(file.id);
    toast.add({ severity: "success", summary: "KYC validated", detail: `${file.full_legal_name} is now active.`, life: 3000 });
    await load();
  } catch (e) {
    toast.add({ severity: "error", summary: "Failed", detail: errorMessage(e), life: 5000 });
  } finally {
    acting.value = false;
  }
}

function openReject(file: KycFile) {
  rejectTarget.value = file;
  rejectReason.value = "";
  rejectVisible.value = true;
}

async function confirmReject() {
  if (!rejectTarget.value) return;
  acting.value = true;
  try {
    await kycApi.reject(rejectTarget.value.id, rejectReason.value);
    rejectVisible.value = false;
    toast.add({ severity: "success", summary: "KYC rejected", life: 2500 });
    await load();
  } catch (e) {
    toast.add({ severity: "error", summary: "Failed", detail: errorMessage(e), life: 5000 });
  } finally {
    acting.value = false;
  }
}
</script>

<template>
  <div class="page">
    <div class="header">
      <h1>KYC queue</h1>
      <Dropdown v-model="statusFilter" :options="statusOptions" option-label="label" option-value="value" class="filter" />
    </div>

    <DataTable :value="files" :loading="loading" striped-rows>
      <Column field="full_legal_name" header="Name" />
      <Column field="country" header="Country" />
      <Column field="id_document_type" header="Document" />
      <Column field="submitted_at" header="Submitted">
        <template #body="{ data }">{{ data.submitted_at ? new Date(data.submitted_at).toLocaleString() : "—" }}</template>
      </Column>
      <Column field="status" header="Status">
        <template #body="{ data }"><Tag :value="data.status" /></template>
      </Column>
      <Column v-if="statusFilter === 'submitted'" header="Actions">
        <template #body="{ data }">
          <div class="actions">
            <Button label="Validate" size="small" severity="success" :loading="acting" @click="validate(data)" />
            <Button label="Reject" size="small" severity="danger" outlined :loading="acting" @click="openReject(data)" />
          </div>
        </template>
      </Column>
    </DataTable>
    <p v-if="!loading && files.length === 0" class="empty">No KYC files in this status.</p>

    <Dialog v-model:visible="rejectVisible" header="Reject KYC" modal :style="{ width: '380px' }">
      <label>
        Reason
        <Textarea v-model="rejectReason" rows="3" fluid autofocus />
      </label>
      <template #footer>
        <Button label="Cancel" severity="secondary" @click="rejectVisible = false" />
        <Button label="Reject" severity="danger" :loading="acting" :disabled="!rejectReason" @click="confirmReject" />
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
  flex-wrap: wrap;
  gap: 0.75rem;
}
.filter {
  min-width: 260px;
}
.actions {
  display: flex;
  gap: 0.5rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
  font-size: 0.9rem;
}
.empty {
  color: var(--text-muted);
}
</style>
