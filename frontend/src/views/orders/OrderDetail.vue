<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Message from "primevue/message";
import Tag from "primevue/tag";
import { useConfirm } from "primevue/useconfirm";
import { useToast } from "primevue/usetoast";
import { onMounted, ref } from "vue";

import { errorMessage } from "@/api/http";
import { ledgerApi } from "@/api/ledger";
import { marketApi } from "@/api/market";
import { ordersApi } from "@/api/orders";
import type { Execution, Instrument, LedgerEntry, Order } from "@/api/types";

const props = defineProps<{ id: string }>();
const confirm = useConfirm();
const toast = useToast();

const order = ref<Order | null>(null);
const instrument = ref<Instrument | null>(null);
const executions = ref<Execution[]>([]);
const ledgerEntries = ref<LedgerEntry[]>([]);
const loading = ref(true);
const cancelling = ref(false);

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
    order.value = await ordersApi.get(props.id);
    executions.value = await ordersApi.executions(props.id);
    const [allInstruments, allLedger] = await Promise.all([marketApi.list(), ledgerApi.getMine()]);
    instrument.value = allInstruments.find((i) => i.id === order.value!.instrument_id) ?? null;
    ledgerEntries.value = allLedger.filter((e) => e.order_id === props.id);
  } finally {
    loading.value = false;
  }
}

onMounted(load);

function confirmCancel() {
  confirm.require({
    message: "Cancel this order? Any reserved funds or shares will be released.",
    header: "Cancel order",
    acceptLabel: "Cancel order",
    rejectLabel: "Keep order",
    accept: doCancel,
  });
}

async function doCancel() {
  cancelling.value = true;
  try {
    order.value = await ordersApi.cancel(props.id);
    toast.add({ severity: "success", summary: "Order cancelled", life: 2500 });
  } catch (e) {
    toast.add({ severity: "error", summary: "Could not cancel", detail: errorMessage(e), life: 5000 });
  } finally {
    cancelling.value = false;
  }
}
</script>

<template>
  <div v-if="order" class="page">
    <div class="header">
      <h1>Order {{ order.side }} {{ order.quantity }} {{ instrument?.symbol ?? "" }}</h1>
      <Tag :value="order.status" :severity="statusSeverity[order.status] ?? 'secondary'" />
    </div>

    <Message v-if="order.status === 'rejected'" severity="warn" :closable="false">
      Rejected: {{ order.rejection_reason }}
    </Message>

    <Card>
      <template #title>Order details</template>
      <template #content>
        <dl>
          <dt>Instrument</dt>
          <dd>{{ instrument?.symbol }} — {{ instrument?.name }}</dd>
          <dt>Side</dt>
          <dd>{{ order.side }}</dd>
          <dt>Type</dt>
          <dd>{{ order.order_type }}<span v-if="order.limit_price"> @ ${{ order.limit_price }}</span></dd>
          <dt>Quantity</dt>
          <dd>{{ order.quantity }}</dd>
          <dt>Estimated amount</dt>
          <dd>{{ order.estimated_amount ? `$${order.estimated_amount}` : "—" }}</dd>
          <dt>Estimated fees</dt>
          <dd>{{ order.estimated_fees ? `$${order.estimated_fees}` : "—" }}</dd>
          <dt>Created</dt>
          <dd>{{ new Date(order.created_at).toLocaleString() }}</dd>
          <dt v-if="order.executed_at">Executed</dt>
          <dd v-if="order.executed_at">{{ new Date(order.executed_at).toLocaleString() }}</dd>
          <dt v-if="order.cancelled_at">Cancelled</dt>
          <dd v-if="order.cancelled_at">{{ new Date(order.cancelled_at).toLocaleString() }}</dd>
        </dl>
        <Button
          v-if="order.status === 'reserved'"
          label="Cancel order"
          severity="danger"
          :loading="cancelling"
          @click="confirmCancel"
        />
      </template>
    </Card>

    <Card v-if="executions.length">
      <template #title>Execution(s)</template>
      <template #content>
        <DataTable :value="executions">
          <Column field="executed_at" header="Time">
            <template #body="{ data }">{{ new Date(data.executed_at).toLocaleString() }}</template>
          </Column>
          <Column field="price" header="Price">
            <template #body="{ data }">${{ data.price }}</template>
          </Column>
          <Column field="quantity" header="Qty" />
          <Column field="fees" header="Fee">
            <template #body="{ data }">${{ data.fees }}</template>
          </Column>
          <Column field="net_amount" header="Net">
            <template #body="{ data }">${{ data.net_amount }}</template>
          </Column>
        </DataTable>
      </template>
    </Card>

    <Card v-if="ledgerEntries.length">
      <template #title>Linked ledger entries</template>
      <template #content>
        <DataTable :value="ledgerEntries">
          <Column field="created_at" header="Time">
            <template #body="{ data }">{{ new Date(data.created_at).toLocaleString() }}</template>
          </Column>
          <Column field="entry_type" header="Type" />
          <Column field="amount" header="Amount">
            <template #body="{ data }">
              <span :class="Number(data.amount) < 0 ? 'neg' : 'pos'">${{ data.amount }}</span>
            </template>
          </Column>
          <Column field="balance_after" header="Balance after">
            <template #body="{ data }">${{ data.balance_after }}</template>
          </Column>
          <Column field="reference" header="Reference" />
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
.header {
  display: flex;
  align-items: center;
  gap: 1rem;
}
dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1rem;
  margin: 0 0 1rem;
}
dt {
  font-weight: 600;
  color: var(--p-text-muted-color);
}
dd {
  margin: 0;
}
.pos {
  color: var(--p-green-600);
  font-weight: 600;
}
.neg {
  color: var(--p-red-600);
  font-weight: 600;
}
</style>
