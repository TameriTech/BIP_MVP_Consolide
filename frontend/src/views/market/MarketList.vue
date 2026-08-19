<script setup lang="ts">
import InputText from "primevue/inputtext";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { useMarketStore } from "@/stores/market";

const market = useMarketStore();
const router = useRouter();
const search = ref("");
const sectorFilter = ref("All");

onMounted(() => market.fetchAll());

const sectors = computed(() => {
  const all = market.instruments.map((i) => i.sector).filter(Boolean) as string[];
  return ["All", ...Array.from(new Set(all)).sort()];
});

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase();
  return market.instruments.filter((i) => {
    const matchSearch = !q || i.symbol.toLowerCase().includes(q) || i.name.toLowerCase().includes(q);
    const matchSector = sectorFilter.value === "All" || i.sector === sectorFilter.value;
    return matchSearch && matchSector;
  });
});

function open(symbol: string) {
  router.push({ name: "market-detail", params: { symbol } });
}

function fmtPrice(val: string | null) {
  if (!val) return "—";
  return Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
</script>

<template>
  <div class="page animate-fade-in">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1>Market</h1>
        <p class="sub">{{ filtered.length }} instruments · BRVM simulated data</p>
      </div>
      <div class="sim-pill">
        <span class="live-dot"></span>
        Live simulated prices
      </div>
    </div>

    <!-- Filters -->
    <div class="filters">
      <div class="search-wrap">
        <i class="pi pi-search search-icon"></i>
        <InputText
          v-model="search"
          placeholder="Search symbol or company…"
          class="search-input"
        />
      </div>
      <div class="sector-filters">
        <button
          v-for="s in sectors"
          :key="s"
          class="sector-chip"
          :class="{ active: sectorFilter === s }"
          @click="sectorFilter = s"
        >
          {{ s }}
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="table-wrap">
      <!-- Loading skeleton -->
      <div v-if="market.loading" class="loading-rows">
        <div v-for="i in 8" :key="i" class="skeleton-row">
          <div class="skel skel-sm"></div>
          <div class="skel skel-lg"></div>
          <div class="skel skel-md"></div>
          <div class="skel skel-md"></div>
          <div class="skel skel-sm"></div>
        </div>
      </div>

      <div v-else class="table-scroll">
      <table class="market-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Company</th>
            <th>Sector</th>
            <th>Last Price (XOF)</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="inst in filtered"
            :key="inst.id"
            class="market-row"
            @click="open(inst.symbol)"
          >
            <td>
              <div class="symbol-cell">
                <div class="symbol-badge">{{ inst.symbol.slice(0, 2) }}</div>
                <span class="symbol-text">{{ inst.symbol }}</span>
              </div>
            </td>
            <td class="company-cell">{{ inst.name }}</td>
            <td>
              <span v-if="inst.sector" class="sector-tag">{{ inst.sector }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="price-cell num">
              {{ fmtPrice(inst.last_price) }}
            </td>
            <td>
              <span class="status-badge" :class="inst.tradable ? 'badge-success' : 'badge-danger'">
                <span class="status-dot"></span>
                {{ inst.tradable ? "Tradable" : "Halted" }}
              </span>
            </td>
          </tr>
          <tr v-if="filtered.length === 0">
            <td colspan="5" class="empty-cell">
              <i class="pi pi-search"></i>
              No instruments match your search.
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 1.5rem; }

.sub {
  font-size: var(--text-sm);
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.sim-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--bip-green);
  background: rgba(16,185,129,0.08);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: 99px;
  padding: 0.35rem 0.875rem;
}

/* Filters */
.filters { display: flex; flex-wrap: wrap; gap: 0.875rem; align-items: center; }
.search-wrap {
  position: relative;
  flex: 1;
  min-width: 220px;
  max-width: 360px;
}
.search-icon {
  position: absolute;
  left: 0.875rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: var(--text-sm);
  pointer-events: none;
}
.search-input { width: 100%; padding-left: 2.5rem !important; }

.sector-filters { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.sector-chip {
  padding: 0.3rem 0.75rem;
  border-radius: 99px;
  border: 1px solid var(--surface-border-strong);
  background: var(--surface-2);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.sector-chip:hover { background: var(--surface-3); color: var(--text-primary); }
.sector-chip.active {
  background: rgba(240,180,41,0.12);
  border-color: rgba(240,180,41,0.35);
  color: var(--bip-gold);
}

/* Table */
.table-wrap {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.table-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.market-table {
  width: 100%;
  min-width: 640px;
  border-collapse: collapse;
}
.market-table thead tr {
  background: var(--surface-2);
  border-bottom: 1px solid var(--surface-border);
}
.market-table th {
  padding: 0.875rem 1.25rem;
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--text-secondary);
  white-space: nowrap;
}
.market-row {
  cursor: pointer;
  border-bottom: 1px solid var(--surface-border);
  transition: background var(--transition-fast);
}
.market-row:hover { background: var(--surface-2); }
.market-row:last-child { border-bottom: none; }
.market-table td { padding: 0.9rem 1.25rem; vertical-align: middle; }

/* Symbol cell */
.symbol-cell { display: flex; align-items: center; gap: 0.625rem; }
.symbol-badge {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--surface-3), var(--surface-2));
  border: 1px solid var(--surface-border-strong);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-2xs);
  font-weight: 800;
  color: var(--bip-gold);
  flex-shrink: 0;
}
.symbol-text { font-weight: 700; font-size: var(--text-base); color: var(--text-primary); }

.company-cell { color: var(--text-secondary); font-size: var(--text-sm); max-width: 260px; }

.sector-tag {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  background: var(--surface-2);
  border: 1px solid var(--surface-border);
  border-radius: 99px;
  padding: 0.15rem 0.55rem;
}

.price-cell {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', monospace;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: var(--text-2xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  padding: 0.2rem 0.65rem;
  border-radius: 99px;
}
.badge-success { background: rgba(16,185,129,0.12); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
.badge-danger  { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.empty-cell {
  text-align: center;
  padding: 3rem !important;
  color: var(--text-muted);
  font-size: var(--text-base);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}
.empty-cell .pi { font-size: 1.75rem; margin-bottom: 0.25rem; }

/* Skeleton */
.loading-rows { display: flex; flex-direction: column; gap: 0; }
.skeleton-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  border-bottom: 1px solid var(--surface-border);
}
.skel {
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--surface-2) 0%, var(--surface-3) 50%, var(--surface-2) 100%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite linear;
}
.skel-sm  { width: 60px; }
.skel-md  { width: 120px; }
.skel-lg  { flex: 1; }
@keyframes shimmer {
  from { background-position: 200% center; }
  to   { background-position: -200% center; }
}
</style>
