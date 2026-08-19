<script setup lang="ts">
import Button from "primevue/button";
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

function fmt(val: string | null | undefined) {
  if (val === null || val === undefined) return "—";
  return `${Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} XOF`;
}

function fmtDate(d: string) {
  return new Date(d).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

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
  <div v-if="order" class="page animate-fade-in">
    <div class="header">
      <div class="header-left">
        <div class="side-icon" :class="order.side === 'buy' ? 'icon-buy' : 'icon-sell'">
          <i :class="order.side === 'buy' ? 'pi pi-arrow-up-right' : 'pi pi-arrow-down-right'"></i>
        </div>
        <div>
          <h1>{{ order.side === "buy" ? "Buy" : "Sell" }} {{ order.quantity }} {{ instrument?.symbol ?? "" }}</h1>
          <p class="sub">{{ instrument?.name }}</p>
        </div>
      </div>
      <Tag :value="order.status.toUpperCase()" :severity="statusSeverity[order.status] ?? 'secondary'" />
    </div>

    <Message v-if="order.status === 'rejected'" severity="warn" :closable="false">
      Rejected: {{ order.rejection_reason }}
    </Message>

    <div class="panel">
      <div class="panel-header"><h2>Order details</h2></div>
      <div class="panel-body">
        <dl>
          <dt>Instrument</dt>
          <dd>{{ instrument?.symbol }} — {{ instrument?.name }}</dd>
          <dt>Side</dt>
          <dd class="capitalize">{{ order.side }}</dd>
          <dt>Type</dt>
          <dd class="capitalize">{{ order.order_type }}<span v-if="order.limit_price" class="num"> @ {{ fmt(order.limit_price) }}</span></dd>
          <dt>Quantity</dt>
          <dd class="num">{{ order.quantity }}</dd>
          <dt>Estimated amount</dt>
          <dd class="num">{{ fmt(order.estimated_amount) }}</dd>
          <dt>Estimated fees</dt>
          <dd class="num">{{ fmt(order.estimated_fees) }}</dd>
          <dt>Created</dt>
          <dd>{{ fmtDate(order.created_at) }}</dd>
          <template v-if="order.executed_at">
            <dt>Executed</dt>
            <dd>{{ fmtDate(order.executed_at) }}</dd>
          </template>
          <template v-if="order.cancelled_at">
            <dt>Cancelled</dt>
            <dd>{{ fmtDate(order.cancelled_at) }}</dd>
          </template>
        </dl>
        <Button
          v-if="order.status === 'reserved'"
          label="Cancel order"
          severity="danger"
          :loading="cancelling"
          class="cancel-btn"
          @click="confirmCancel"
        />
      </div>
    </div>

    <div v-if="executions.length" class="panel">
      <div class="panel-header"><h2>Execution(s)</h2></div>
      <DataTable :value="executions">
        <Column field="executed_at" header="Time">
          <template #body="{ data }">{{ fmtDate(data.executed_at) }}</template>
        </Column>
        <Column field="price" header="Price">
          <template #body="{ data }"><span class="num">{{ fmt(data.price) }}</span></template>
        </Column>
        <Column field="quantity" header="Qty" />
        <Column field="fees" header="Fee">
          <template #body="{ data }"><span class="num">{{ fmt(data.fees) }}</span></template>
        </Column>
        <Column field="net_amount" header="Net">
          <template #body="{ data }"><span class="num">{{ fmt(data.net_amount) }}</span></template>
        </Column>
      </DataTable>
    </div>

    <div v-if="ledgerEntries.length" class="panel">
      <div class="panel-header"><h2>Linked ledger entries</h2></div>
      <DataTable :value="ledgerEntries">
        <Column field="created_at" header="Time">
          <template #body="{ data }">{{ fmtDate(data.created_at) }}</template>
        </Column>
        <Column field="entry_type" header="Type" />
        <Column field="amount" header="Amount">
          <template #body="{ data }">
            <span class="num" :class="Number(data.amount) < 0 ? 'neg' : 'pos'">{{ fmt(data.amount) }}</span>
          </template>
        </Column>
        <Column field="balance_after" header="Balance after">
          <template #body="{ data }"><span class="num">{{ fmt(data.balance_after) }}</span></template>
        </Column>
        <Column field="reference" header="Reference">
          <template #body="{ data }"><code>{{ data.reference }}</code></template>
        </Column>
      </DataTable>
    </div>
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
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.header-left { display: flex; align-items: center; gap: 0.875rem; }
.side-icon {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; flex-shrink: 0;
}
.icon-buy  { background: rgba(16,185,129,0.12); color: var(--bip-green); }
.icon-sell { background: rgba(239,68,68,0.12);  color: var(--bip-red); }
.header h1 { margin: 0; }
.sub { font-size: var(--text-sm); color: var(--text-muted); margin-top: 2px; }

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

dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.7rem 1.5rem;
  margin: 0 0 1.25rem;
}
dt {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-muted);
}
dd {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-primary);
}
.capitalize { text-transform: capitalize; }
.cancel-btn { margin-top: 0.5rem; }

.pos { color: var(--bip-green) !important; font-weight: 600; }
.neg { color: var(--bip-red) !important; font-weight: 600; }

code {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--text-xs);
  color: var(--bip-gold);
  background: rgba(240,180,41,0.07);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}
</style>
