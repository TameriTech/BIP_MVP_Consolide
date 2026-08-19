<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { ledgerApi } from "@/api/ledger";
import type { LedgerEntry, LedgerEntryType } from "@/api/types";

const entries = ref<LedgerEntry[]>([]);
const loading = ref(true);
const typeFilter = ref<LedgerEntryType | null>(null);

const typeOptions: { label: string; value: LedgerEntryType | null }[] = [
  { label: "All", value: null },
  { label: "Initial credit", value: "initial_credit" },
  { label: "Buy", value: "trade_buy" },
  { label: "Sell", value: "trade_sell" },
  { label: "Fee", value: "fee" },
];

const entryTypeConfig: Record<string, { label: string; cls: string; icon: string }> = {
  initial_credit: { label: "Initial Credit", cls: "type-credit",  icon: "pi-plus-circle" },
  trade_buy:      { label: "Buy",            cls: "type-buy",     icon: "pi-arrow-up-right" },
  trade_sell:     { label: "Sell",           cls: "type-sell",    icon: "pi-arrow-down-right" },
  fee:            { label: "Fee",            cls: "type-fee",     icon: "pi-minus-circle" },
};

async function load() {
  loading.value = true;
  try {
    entries.value = await ledgerApi.getMine(typeFilter.value ? { entry_type: typeFilter.value } : undefined);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(typeFilter, load);

function fmt(val: string) {
  const n = Number(val);
  return (n >= 0 ? "+" : "") + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtBalance(val: string) {
  return Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(d: string) {
  return new Date(d).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}
</script>

<template>
  <div class="page animate-fade-in">
    <div class="page-header">
      <div>
        <h1>Transaction Ledger</h1>
        <p class="sub">Immutable record of all account movements</p>
      </div>
    </div>

    <!-- Type filter chips -->
    <div class="filter-row">
      <button
        v-for="opt in typeOptions"
        :key="String(opt.value)"
        class="filter-chip"
        :class="{ active: typeFilter === opt.value }"
        @click="typeFilter = opt.value"
      >
        {{ opt.label }}
      </button>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="ledger-panel">
      <div v-for="i in 8" :key="i" class="skeleton-row">
        <div class="skel skel-md"></div>
        <div class="skel skel-sm"></div>
        <div class="skel skel-md"></div>
        <div class="skel skel-lg"></div>
        <div class="skel skel-sm"></div>
      </div>
    </div>

    <!-- Ledger table -->
    <div v-else-if="entries.length" class="ledger-panel">
      <table class="ledger-table">
        <thead>
          <tr>
            <th>Date & Time</th>
            <th>Type</th>
            <th class="right-align">Amount (XOF)</th>
            <th class="right-align">Balance After (XOF)</th>
            <th>Reference</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in entries" :key="entry.id" class="ledger-row">
            <td class="date-cell">{{ fmtDate(entry.created_at) }}</td>
            <td>
              <span
                class="type-badge"
                :class="(entryTypeConfig[entry.entry_type] ?? entryTypeConfig.fee).cls"
              >
                <i :class="`pi ${(entryTypeConfig[entry.entry_type] ?? entryTypeConfig.fee).icon}`"></i>
                {{ (entryTypeConfig[entry.entry_type] ?? { label: entry.entry_type }).label }}
              </span>
            </td>
            <td class="right-align">
              <span class="amount num" :class="Number(entry.amount) >= 0 ? 'pos' : 'neg'">
                {{ fmt(entry.amount) }}
              </span>
            </td>
            <td class="right-align">
              <span class="balance num">{{ fmtBalance(entry.balance_after) }}</span>
            </td>
            <td class="ref-cell">
              <code v-if="entry.reference">{{ entry.reference }}</code>
              <span v-else class="text-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-panel">
      <i class="pi pi-book"></i>
      <p>No ledger entries found for this filter.</p>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 1.5rem; }
.sub { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem; }

/* Filter chips */
.filter-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.filter-chip {
  padding: 0.3rem 0.875rem;
  border-radius: 99px;
  border: 1px solid var(--surface-border-strong);
  background: var(--surface-2);
  color: var(--text-secondary);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  transition: all var(--transition-fast);
}
.filter-chip:hover { background: var(--surface-3); color: var(--text-primary); }
.filter-chip.active {
  background: rgba(240,180,41,0.12);
  border-color: rgba(240,180,41,0.3);
  color: var(--bip-gold);
}

/* Panel */
.ledger-panel {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.ledger-table { width: 100%; border-collapse: collapse; }
.ledger-table thead tr { background: var(--surface-2); border-bottom: 1px solid var(--surface-border); }
.ledger-table th {
  padding: 0.875rem 1.25rem;
  text-align: left;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
.right-align { text-align: right !important; }
.ledger-row {
  border-bottom: 1px solid var(--surface-border);
  transition: background var(--transition-fast);
}
.ledger-row:hover { background: var(--surface-2); }
.ledger-row:last-child { border-bottom: none; }
.ledger-table td { padding: 0.875rem 1.25rem; vertical-align: middle; font-size: 0.875rem; }

.date-cell { font-size: 0.78rem; color: var(--text-muted); white-space: nowrap; }

.type-badge {
  display: inline-flex; align-items: center; gap: 0.35rem;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
  padding: 0.2rem 0.65rem; border-radius: 99px;
}
.type-credit { background: rgba(240,180,41,0.12); color: var(--bip-gold); border: 1px solid rgba(240,180,41,0.25); }
.type-buy    { background: rgba(16,185,129,0.12);  color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
.type-sell   { background: rgba(239,68,68,0.12);   color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
.type-fee    { background: rgba(100,116,139,0.1);  color: #94a3b8; border: 1px solid rgba(100,116,139,0.2); }

.amount { font-weight: 700; font-size: 0.9rem; }
.pos { color: var(--bip-green) !important; }
.neg { color: var(--bip-red)   !important; }
.balance { color: var(--text-primary); font-weight: 600; }

.ref-cell code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  color: var(--bip-gold);
  background: rgba(240,180,41,0.07);
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  letter-spacing: 0.01em;
}
.text-muted { color: var(--text-muted); }

/* Empty */
.empty-panel {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 0.75rem; padding: 3rem;
  text-align: center; color: var(--text-muted);
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
}
.empty-panel .pi { font-size: 2.5rem; }
.empty-panel p { font-size: 0.9rem; }

/* Skeleton */
.skeleton-row { display: flex; align-items: center; gap: 1rem; padding: 1rem 1.25rem; border-bottom: 1px solid var(--surface-border); }
.skel { height: 12px; border-radius: 6px; background: var(--surface-2); animation: pulse 1.5s ease infinite alternate; }
.skel-sm { width: 80px; } .skel-md { width: 120px; } .skel-lg { flex: 1; }
@keyframes pulse { from { opacity: 0.5; } to { opacity: 1; } }
</style>
