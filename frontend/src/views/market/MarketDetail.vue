<script setup lang="ts">
import Button from "primevue/button";
import Chart from "primevue/chart";
import Dialog from "primevue/dialog";
import InputNumber from "primevue/inputnumber";
import Message from "primevue/message";
import SelectButton from "primevue/selectbutton";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { errorMessage } from "@/api/http";
import { marketApi } from "@/api/market";
import { ordersApi } from "@/api/orders";
import type { Instrument, Quote } from "@/api/types";

const props = defineProps<{ symbol: string }>();
const router = useRouter();
const toast = useToast();

const instrument = ref<Instrument | null>(null);
const quotes = ref<Quote[]>([]);
const loading = ref(true);

const side = ref<"buy" | "sell">("buy");
const orderType = ref<"market" | "limit">("market");
const quantity = ref<number>(1);
const limitPrice = ref<number | null>(null);
const confirmVisible = ref(false);
const submitting = ref(false);
const submitError = ref("");

async function load() {
  loading.value = true;
  try {
    instrument.value = await marketApi.get(props.symbol);
    quotes.value = await marketApi.quotes(props.symbol);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => props.symbol, load);

const lastPrice = computed(() => (instrument.value?.last_price ? Number(instrument.value.last_price) : 0));
const refPrice  = computed(() => (orderType.value === "limit" && limitPrice.value ? limitPrice.value : lastPrice.value));
const estimatedGross  = computed(() => quantity.value * refPrice.value);
const estimatedFee    = computed(() => estimatedGross.value * 0.001);
const estimatedTotal  = computed(() =>
  side.value === "buy" ? estimatedGross.value + estimatedFee.value : estimatedGross.value - estimatedFee.value,
);

// Chart with gradient fill
const chartData = computed(() => {
  const prices = quotes.value.map((q) => Number(q.price));
  const isUp = prices.length >= 2 ? prices[prices.length - 1] >= prices[0] : true;
  return {
    labels: quotes.value.map((q) => new Date(q.as_of).toLocaleDateString("en-US", { month: "short", day: "numeric" })),
    datasets: [{
      label: props.symbol,
      data: prices,
      borderColor: isUp ? "#10b981" : "#ef4444",
      borderWidth: 2,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 4,
      fill: true,
      backgroundColor: (ctx: any) => {
        const canvas = ctx.chart.ctx;
        const gradient = canvas.createLinearGradient(0, 0, 0, 250);
        if (isUp) {
          gradient.addColorStop(0, "rgba(16,185,129,0.25)");
          gradient.addColorStop(1, "rgba(16,185,129,0)");
        } else {
          gradient.addColorStop(0, "rgba(239,68,68,0.2)");
          gradient.addColorStop(1, "rgba(239,68,68,0)");
        }
        return gradient;
      },
    }],
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => ` ${Number(ctx.raw).toLocaleString("en-US", { minimumFractionDigits: 2 })} XOF`,
      },
      backgroundColor: "#161d2e",
      borderColor: "rgba(255,255,255,0.1)",
      borderWidth: 1,
      titleColor: "#94a3b8",
      bodyColor: "#f1f5f9",
      padding: 10,
    },
  },
  scales: {
    x: {
      grid: { color: "rgba(255,255,255,0.04)", drawBorder: false },
      ticks: { color: "#6b7a94", font: { size: 10 }, maxTicksLimit: 6 },
    },
    y: {
      grid: { color: "rgba(255,255,255,0.04)", drawBorder: false },
      ticks: {
        color: "#6b7a94",
        font: { size: 10, family: "JetBrains Mono" },
        callback: (v: number) => v.toLocaleString("en-US", { maximumFractionDigits: 0 }),
      },
      beginAtZero: false,
    },
  },
  interaction: { intersect: false, mode: "index" as const },
};

function openConfirm() {
  submitError.value = "";
  confirmVisible.value = true;
}

async function confirmSubmit() {
  if (!instrument.value) return;
  submitting.value = true;
  submitError.value = "";
  try {
    const order = await ordersApi.submit({
      instrument_id: instrument.value.id,
      side: side.value,
      order_type: orderType.value,
      quantity: String(quantity.value),
      limit_price: orderType.value === "limit" && limitPrice.value ? String(limitPrice.value) : undefined,
    });
    confirmVisible.value = false;
    if (order.status === "executed") {
      toast.add({ severity: "success", summary: "Order executed", detail: `${side.value.toUpperCase()} ${quantity.value} ${props.symbol}`, life: 3500 });
    } else if (order.status === "rejected") {
      toast.add({ severity: "warn", summary: "Order rejected", detail: order.rejection_reason ?? "", life: 5000 });
    }
    router.push({ name: "order-detail", params: { id: order.id } });
  } catch (e) {
    submitError.value = errorMessage(e);
  } finally {
    submitting.value = false;
  }
}

function fmtPrice(val: string | null) {
  if (!val) return "—";
  return Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const priceChange = computed(() => {
  if (quotes.value.length < 2) return null;
  const first = Number(quotes.value[0].price);
  const last  = Number(quotes.value[quotes.value.length - 1].price);
  const pct   = ((last - first) / first) * 100;
  return { pct, up: pct >= 0, diff: last - first };
});

const stats24h = computed(() => {
  if (!quotes.value.length) return null;
  const prices = quotes.value.map((q) => Number(q.price));
  return {
    high: Math.max(...prices),
    low: Math.min(...prices),
  };
});
</script>

<template>
  <div v-if="loading" class="page-loading">
    <div class="skeleton-header"></div>
    <div class="skeleton-chart"></div>
  </div>

  <div v-else-if="instrument" class="page animate-fade-in">
    <!-- Breadcrumb -->
    <div class="breadcrumb">
      <button @click="router.push({ name: 'market-list' })">
        <i class="pi pi-arrow-left"></i> Market
      </button>
      <span class="bc-sep">/</span>
      <span>{{ instrument.symbol }}</span>
    </div>

    <!-- Instrument header -->
    <div class="instrument-header">
      <div class="inst-left">
        <div class="inst-badge">{{ instrument.symbol.slice(0, 2) }}</div>
        <div>
          <div class="inst-title">
            <h1>{{ instrument.symbol }}</h1>
            <span class="status-pill" :class="instrument.tradable ? 'badge-success' : 'badge-danger'">
              <span class="status-dot"></span>
              {{ instrument.tradable ? "Tradable" : "Halted" }}
            </span>
          </div>
          <p class="inst-name">{{ instrument.name }}</p>
          <p class="inst-meta">
            <span>{{ instrument.market }}</span>
            <span v-if="instrument.sector" class="meta-sep">·</span>
            <span v-if="instrument.sector">{{ instrument.sector }}</span>
            <span class="meta-sep">·</span>
            <span>{{ instrument.currency }}</span>
          </p>
        </div>
      </div>
      <div v-if="stats24h" class="inst-stats">
        <div class="stat-item">
          <div class="stat-label">24h High</div>
          <div class="stat-val num">{{ fmtPrice(String(stats24h.high)) }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">24h Low</div>
          <div class="stat-val num">{{ fmtPrice(String(stats24h.low)) }}</div>
        </div>
      </div>
      <div class="inst-price-block">
        <div class="inst-price num">{{ fmtPrice(instrument.last_price) }}</div>
        <div v-if="priceChange" class="price-change" :class="priceChange.up ? 'change-pos' : 'change-neg'">
          <span class="change-diff">{{ priceChange.up ? '+' : '' }}{{ priceChange.diff.toLocaleString("en-US", { minimumFractionDigits: 2 }) }}</span>
          <span class="change-pct">({{ priceChange.pct.toFixed(2) }}%)</span>
        </div>
        <div class="currency-label">XOF</div>
      </div>
    </div>

    <!-- Main 2-column layout -->
    <div class="main-cols">
      <!-- Left: chart -->
      <div class="chart-panel">
        <div class="chart-header">
          <h2>Price History</h2>
          <span class="chart-hint">Simulated demo data</span>
        </div>
        <div v-if="quotes.length" class="chart-wrap">
          <Chart type="line" :data="chartData" :options="chartOptions" />
        </div>
        <div v-else class="chart-empty">
          <i class="pi pi-chart-line"></i>
          <p>No price history available yet.</p>
        </div>
      </div>

      <!-- Right: order ticket -->
      <div class="order-ticket">
        <div class="ticket-header">
          <h2>Place Order</h2>
          <span v-if="!instrument.tradable" class="halt-badge">
            <i class="pi pi-ban"></i> Trading halted
          </span>
        </div>

        <!-- Side selector -->
        <div class="side-selector">
          <button
            class="side-btn"
            :class="{ 'side-buy-active': side === 'buy' }"
            @click="side = 'buy'"
          >
            <i class="pi pi-arrow-up-right"></i>
            Buy
          </button>
          <button
            class="side-btn"
            :class="{ 'side-sell-active': side === 'sell' }"
            @click="side = 'sell'"
          >
            <i class="pi pi-arrow-down-right"></i>
            Sell
          </button>
        </div>

        <!-- Order type tabs -->
        <div class="ticket-tabs">
          <button class="ticket-tab" :class="{ 'tab-active': orderType === 'market' }" @click="orderType = 'market'">Market</button>
          <button class="ticket-tab" :class="{ 'tab-active': orderType === 'limit' }" @click="orderType = 'limit'">Limit</button>
        </div>

        <!-- Quantity -->
        <div class="ticket-section">
          <div class="section-label">Quantity</div>
          <InputNumber
            v-model="quantity"
            :min="1"
            :max-fraction-digits="0"
            show-buttons
            fluid
            style="width:100%"
          />
        </div>

        <!-- Limit price -->
        <div v-if="orderType === 'limit'" class="ticket-section">
          <div class="section-label">Limit price (XOF)</div>
          <InputNumber
            v-model="limitPrice"
            :min="0"
            :max-fraction-digits="2"
            fluid
            style="width:100%"
          />
        </div>

        <!-- Estimate box -->
        <div class="estimate-box" :class="side === 'buy' ? 'est-buy' : 'est-sell'">
          <div class="est-row">
            <span>Gross amount</span>
            <span class="num">{{ estimatedGross.toLocaleString("en-US", { minimumFractionDigits: 2 }) }} XOF</span>
          </div>
          <div class="est-row est-fee">
            <span>Commission (0.1%)</span>
            <span class="num">{{ estimatedFee.toLocaleString("en-US", { minimumFractionDigits: 2 }) }} XOF</span>
          </div>
          <div class="est-divider"></div>
          <div class="est-row est-total">
            <span>{{ side === "buy" ? "Total cost" : "Net proceeds" }}</span>
            <span class="num">{{ estimatedTotal.toLocaleString("en-US", { minimumFractionDigits: 2 }) }} XOF</span>
          </div>
        </div>

        <!-- Submit -->
        <button
          class="submit-order"
          :class="side === 'buy' ? 'submit-buy' : 'submit-sell'"
          :disabled="!instrument.tradable || quantity <= 0 || (orderType === 'limit' && !limitPrice)"
          @click="openConfirm"
        >
          <i :class="side === 'buy' ? 'pi pi-arrow-up-right' : 'pi pi-arrow-down-right'"></i>
          {{ side === "buy" ? `Buy ${instrument.symbol}` : `Sell ${instrument.symbol}` }}
        </button>
      </div>
    </div>

    <!-- Confirm dialog -->
    <Dialog v-model:visible="confirmVisible" header="Confirm order" modal :style="{ width: '400px' }">
      <div class="confirm-body">
        <div class="confirm-icon" :class="side === 'buy' ? 'conf-buy' : 'conf-sell'">
          <i :class="side === 'buy' ? 'pi pi-arrow-up-right' : 'pi pi-arrow-down-right'"></i>
        </div>
        <div class="confirm-title">
          {{ side === "buy" ? "Buy" : "Sell" }} {{ quantity }} {{ instrument.symbol }}
        </div>
        <div class="confirm-sub">
          at {{ orderType === "limit" ? `limit ${fmtPrice(String(limitPrice))} XOF` : "market price" }}
        </div>
        <div class="confirm-total">
          <span>{{ side === "buy" ? "Total cost" : "Net proceeds" }}</span>
          <span class="num">{{ estimatedTotal.toLocaleString("en-US", { minimumFractionDigits: 2 }) }} XOF</span>
        </div>
        <Message v-if="submitError" severity="error" :closable="false">{{ submitError }}</Message>
      </div>
      <template #footer>
        <div class="confirm-footer">
          <Button label="Cancel" severity="secondary" @click="confirmVisible = false" />
          <Button
            :label="`Confirm ${side}`"
            :severity="side === 'buy' ? 'success' : 'danger'"
            :loading="submitting"
            @click="confirmSubmit"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 1.5rem; }

/* Breadcrumb */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-sm);
  color: var(--text-muted);
}
.breadcrumb button {
  background: none;
  border: none;
  color: var(--bip-gold);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0;
  transition: color var(--transition-fast);
}
.breadcrumb button:hover { color: var(--bip-gold-light); }
.bc-sep { color: var(--surface-border-strong); }

/* Instrument header */
.instrument-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1.5rem;
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}
.inst-left { display: flex; align-items: flex-start; gap: 1rem; }
.inst-badge {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #1e2840, #2d3a55);
  border: 2px solid var(--surface-border-strong);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: 800;
  color: var(--bip-gold);
  flex-shrink: 0;
}
.inst-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.2rem;
}
.inst-title h1 { margin: 0; }
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: var(--text-2xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  padding: 0.2rem 0.65rem;
  border-radius: 99px;
}
.badge-success { background: rgba(16,185,129,0.12); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
.badge-danger  { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
.status-dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.inst-name { font-size: var(--text-base); color: var(--text-secondary); margin: 0 0 0.25rem; }
.inst-meta { font-size: var(--text-xs); color: var(--text-muted); display: flex; gap: 0.5rem; }
.meta-sep { opacity: 0.4; }

.inst-price-block { text-align: right; }
.inst-price {
  font-size: var(--text-3xl);
  font-weight: 800;
  letter-spacing: var(--tracking-tight);
  color: var(--text-primary);
  line-height: 1;
  font-family: 'JetBrains Mono', monospace;
}
.price-change {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: var(--text-sm);
  font-weight: 700;
  margin-top: 0.35rem;
}
.change-pos { color: var(--bip-green); }
.change-neg { color: var(--bip-red); }
.change-diff { font-weight: 700; margin-right: 0.2rem; }
.change-pct { opacity: 0.8; }
.currency-label { font-size: var(--text-xs); color: var(--text-muted); margin-top: 0.25rem; }

.inst-stats {
  display: flex;
  gap: 2rem;
  margin-left: auto;
  margin-right: 2rem;
  padding-right: 2rem;
  border-right: 1px solid var(--surface-border);
}
@media (max-width: 768px) {
  .inst-stats { display: none; }
}
.stat-item { display: flex; flex-direction: column; gap: 0.1rem; }
.stat-label { font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: var(--tracking-label); }
.stat-val { font-size: var(--text-sm); font-weight: 700; color: var(--text-primary); }

/* Main layout */
.main-cols {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 1.25rem;
  align-items: start;
}
@media (max-width: 900px) { .main-cols { grid-template-columns: 1fr; } }

/* Chart panel */
.chart-panel {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-card);
}
.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.chart-header h2 {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--text-secondary);
}
.chart-hint { font-size: var(--text-xs); color: var(--text-muted); }
.chart-wrap { height: 280px; }
.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-muted);
  gap: 0.5rem;
}
.chart-empty .pi { font-size: 2rem; }

/* Order ticket */
.order-ticket {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}
.ticket-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ticket-header h2 {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--text-secondary);
  margin: 0;
}
.halt-badge {
  font-size: var(--text-xs);
  font-weight: 600;
  color: #f87171;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

/* Side selector */
.side-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  background: var(--surface-2);
  border: 1px solid var(--surface-border-strong);
  border-radius: var(--radius-md);
  padding: 4px;
}
.side-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.6rem;
  border-radius: calc(var(--radius-md) - 2px);
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}
.side-buy-active {
  background: rgba(16,185,129,0.15);
  color: #34d399;
  box-shadow: 0 2px 8px rgba(16,185,129,0.15);
}
.side-sell-active {
  background: rgba(239,68,68,0.15);
  color: #f87171;
  box-shadow: 0 2px 8px rgba(239,68,68,0.15);
}
.side-btn:hover:not(.side-buy-active):not(.side-sell-active) {
  background: var(--surface-3);
  color: var(--text-primary);
}

.ticket-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--surface-border-strong);
  margin-bottom: 0.5rem;
}
.ticket-tab {
  flex: 1;
  background: transparent;
  border: none;
  padding: 0.6rem 0;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all var(--transition-fast);
}
.ticket-tab:hover { color: var(--text-primary); }
.ticket-tab.tab-active {
  color: var(--bip-gold);
  border-bottom-color: var(--bip-gold);
}

.ticket-section { display: flex; flex-direction: column; gap: 0.4rem; }
.section-label {
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--text-secondary);
}

/* Estimate box */
.estimate-box {
  border-radius: var(--radius-md);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border: 1px solid;
}
.est-buy  { background: rgba(16,185,129,0.05); border-color: rgba(16,185,129,0.2); }
.est-sell { background: rgba(239,68,68,0.05);  border-color: rgba(239,68,68,0.2); }
.est-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
.est-fee { font-size: var(--text-xs); color: var(--text-muted); }
.est-divider {
  height: 1px;
  background: var(--surface-border);
  margin: 0.1rem 0;
}
.est-total {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--text-primary);
}

/* Submit button */
.submit-order {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: 700;
  width: 100%;
  transition: all var(--transition-fast);
  letter-spacing: var(--tracking-wide);
}
.submit-buy {
  background: linear-gradient(135deg, #059669, #047857);
  color: white;
  box-shadow: 0 4px 16px rgba(5,150,105,0.35);
}
.submit-buy:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(5,150,105,0.45);
}
.submit-sell {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  color: white;
  box-shadow: 0 4px 16px rgba(220,38,38,0.35);
}
.submit-sell:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(220,38,38,0.45);
}
.submit-order:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* Confirm dialog */
.confirm-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  text-align: center;
  padding: 0.5rem 0 1rem;
}
.confirm-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}
.conf-buy  { background: rgba(16,185,129,0.15); color: #34d399; }
.conf-sell { background: rgba(239,68,68,0.15);  color: #f87171; }
.confirm-title { font-size: var(--text-lg); font-weight: 800; letter-spacing: var(--tracking-snug); color: var(--text-primary); }
.confirm-sub   { font-size: var(--text-sm); color: var(--text-secondary); }
.confirm-total {
  display: flex;
  justify-content: space-between;
  width: 100%;
  background: var(--surface-3);
  border: 1px solid var(--surface-border-strong);
  border-radius: var(--radius-md);
  padding: 0.875rem 1rem;
  font-weight: 700;
  font-size: var(--text-base);
  color: var(--text-primary);
  margin-top: 0.25rem;
}
.confirm-footer { display: flex; justify-content: flex-end; gap: 0.75rem; }

/* Skeleton */
.page-loading { display: flex; flex-direction: column; gap: 1.5rem; }
.skeleton-header {
  height: 120px;
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  animation: shimmer 1.4s infinite linear;
}
.skeleton-chart {
  height: 320px;
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  animation: shimmer 1.4s infinite linear;
}
@keyframes shimmer {
  0%   { opacity: 0.6; }
  50%  { opacity: 1; }
  100% { opacity: 0.6; }
}
</style>
