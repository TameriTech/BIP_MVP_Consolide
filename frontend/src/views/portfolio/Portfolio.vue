<script setup lang="ts">
import Button from "primevue/button";
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { usePortfolioStore } from "@/stores/portfolio";

const portfolio = usePortfolioStore();
const router = useRouter();

onMounted(async () => {
  await portfolio.fetch();
  await portfolio.fetchPerformance();
});

function fmt(val: string | undefined) {
  if (!val) return "—";
  return Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtQty(val: string | undefined) {
  if (!val) return "—";
  return Number(val).toLocaleString("en-US", { maximumFractionDigits: 4 });
}

function plClass(val: string) {
  return Number(val) >= 0 ? "pos" : "neg";
}

function plPrefix(val: string) {
  return Number(val) >= 0 ? "+" : "";
}
</script>

<template>
  <div class="page animate-fade-in">
    <div class="page-header">
      <h1>Portfolio</h1>
      <Button label="Browse market" icon="pi pi-chart-line" severity="secondary" size="small"
        @click="router.push({ name: 'market-list' })" />
    </div>

    <!-- Summary cards -->
    <div v-if="portfolio.portfolio" class="summary-grid">
      <div class="sum-card animate-fade-up stagger-1">
        <div class="sum-icon sum-icon-cash"><i class="pi pi-wallet"></i></div>
        <div>
          <div class="sum-label">Cash Available</div>
          <div class="sum-value num">{{ fmt(portfolio.portfolio.cash_available) }}</div>
          <div class="sum-currency">XOF</div>
        </div>
      </div>
      <div class="sum-card animate-fade-up stagger-2">
        <div class="sum-icon sum-icon-reserved"><i class="pi pi-lock"></i></div>
        <div>
          <div class="sum-label">Cash Reserved</div>
          <div class="sum-value num">{{ fmt(portfolio.portfolio.cash_reserved) }}</div>
          <div class="sum-currency">XOF</div>
        </div>
      </div>
      <div class="sum-card animate-fade-up stagger-3">
        <div class="sum-icon sum-icon-positions"><i class="pi pi-chart-bar"></i></div>
        <div>
          <div class="sum-label">Positions Value</div>
          <div class="sum-value num">{{ fmt(portfolio.portfolio.positions_value) }}</div>
          <div class="sum-currency">XOF</div>
        </div>
      </div>
      <div class="sum-card sum-card-total animate-fade-up stagger-4">
        <div class="sum-icon sum-icon-total"><i class="pi pi-star"></i></div>
        <div>
          <div class="sum-label">Total Value</div>
          <div class="sum-value sum-value-total num">{{ fmt(portfolio.portfolio.total_value) }}</div>
          <div class="sum-currency">XOF</div>
        </div>
      </div>
      <div v-if="portfolio.performance" class="sum-card animate-fade-up stagger-5"
        :class="Number(portfolio.performance.unrealized_pl) >= 0 ? 'sum-card-pos' : 'sum-card-neg'">
        <div class="sum-icon" :class="Number(portfolio.performance.unrealized_pl) >= 0 ? 'sum-icon-pos' : 'sum-icon-neg'">
          <i :class="Number(portfolio.performance.unrealized_pl) >= 0 ? 'pi pi-arrow-up-right' : 'pi pi-arrow-down-right'"></i>
        </div>
        <div>
          <div class="sum-label">Unrealized P&amp;L</div>
          <div class="sum-value num" :class="plClass(portfolio.performance.unrealized_pl)">
            {{ plPrefix(portfolio.performance.unrealized_pl) }}{{ fmt(portfolio.performance.unrealized_pl) }}
          </div>
          <div class="sum-pct" :class="plClass(portfolio.performance.unrealized_pl)">
            {{ plPrefix(portfolio.performance.unrealized_pl_pct) }}{{ Number(portfolio.performance.unrealized_pl_pct).toFixed(2) }}%
          </div>
        </div>
      </div>
    </div>

    <!-- Positions table -->
    <div class="panel animate-fade-up">
      <div class="panel-header">
        <h2>Open Positions</h2>
        <span class="positions-count">{{ portfolio.portfolio?.positions.length ?? 0 }} instruments</span>
      </div>

      <div v-if="portfolio.loading" class="loading-rows">
        <div v-for="i in 4" :key="i" class="skeleton-row">
          <div class="skel skel-sm"></div>
          <div class="skel skel-lg"></div>
          <div class="skel skel-md"></div>
          <div class="skel skel-md"></div>
          <div class="skel skel-md"></div>
        </div>
      </div>

      <table v-else-if="portfolio.portfolio?.positions.length" class="pos-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Quantity</th>
            <th>Reserved</th>
            <th>Avg Cost (XOF)</th>
            <th>Last Price (XOF)</th>
            <th>Market Value (XOF)</th>
            <th>P&amp;L</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="pos in portfolio.portfolio.positions"
            :key="pos.instrument_id"
            class="pos-row"
            @click="router.push({ name: 'market-detail', params: { symbol: pos.symbol } })"
          >
            <td>
              <div class="sym-cell">
                <div class="sym-badge">{{ pos.symbol.slice(0, 2) }}</div>
                <span class="sym-text">{{ pos.symbol }}</span>
              </div>
            </td>
            <td class="num qty-cell">{{ fmtQty(pos.quantity) }}</td>
            <td class="num reserved-cell">
              <span v-if="Number(pos.reserved_quantity) > 0" class="reserved-tag">{{ fmtQty(pos.reserved_quantity) }}</span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="num">{{ fmt(pos.avg_cost) }}</td>
            <td class="num">{{ pos.last_price ? fmt(pos.last_price) : "—" }}</td>
            <td class="num fw-bold">{{ fmt(pos.market_value) }}</td>
            <td>
              <div v-if="pos.last_price" class="pl-cell"
                :class="Number(pos.market_value) >= Number(pos.avg_cost) * Number(pos.quantity) ? 'pos' : 'neg'">
                <span class="num">{{ Number(pos.last_price) >= Number(pos.avg_cost) ? "+" : "" }}{{
                  ((Number(pos.last_price) - Number(pos.avg_cost)) / Number(pos.avg_cost) * 100).toFixed(2)
                }}%</span>
              </div>
              <span v-else class="text-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="empty-state">
        <i class="pi pi-briefcase"></i>
        <p>No open positions yet.</p>
        <Button label="Go to market" size="small" severity="secondary"
          @click="router.push({ name: 'market-list' })" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 1.75rem; }

/* Summary grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}
.sum-card {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: var(--shadow-card);
  transition: transform var(--transition-fast), border-color var(--transition-med);
}
.sum-card:hover { transform: translateY(-2px); border-color: var(--surface-border-strong); }
.sum-card-total { border-color: rgba(240,180,41,0.25) !important; }
.sum-card-pos   { border-color: rgba(16,185,129,0.25) !important; }
.sum-card-neg   { border-color: rgba(239,68,68,0.2)   !important; }

.sum-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}
.sum-icon-cash     { background: rgba(240,180,41,0.12); color: var(--bip-gold); }
.sum-icon-reserved { background: rgba(100,116,139,0.15); color: #94a3b8; }
.sum-icon-positions{ background: rgba(59,130,246,0.12);  color: var(--bip-blue); }
.sum-icon-total    { background: rgba(240,180,41,0.12);  color: var(--bip-gold); }
.sum-icon-pos      { background: rgba(16,185,129,0.12);  color: var(--bip-green); }
.sum-icon-neg      { background: rgba(239,68,68,0.12);   color: var(--bip-red); }

.sum-label   { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.3rem; }
.sum-value   { font-size: 1.35rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; color: var(--text-primary); }
.sum-value-total { color: var(--bip-gold); }
.sum-currency { font-size: 0.68rem; color: var(--text-muted); margin-top: 1px; font-weight: 600; }
.sum-pct { font-size: 0.78rem; font-weight: 700; margin-top: 2px; }

/* Panel */
.panel {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--surface-border);
}
.panel-header h2 {
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin: 0;
}
.positions-count {
  font-size: 0.75rem;
  color: var(--text-muted);
  background: var(--surface-2);
  border: 1px solid var(--surface-border);
  border-radius: 99px;
  padding: 0.15rem 0.6rem;
  font-weight: 600;
}

/* Table */
.pos-table { width: 100%; border-collapse: collapse; }
.pos-table thead tr { background: var(--surface-2); border-bottom: 1px solid var(--surface-border); }
.pos-table th {
  padding: 0.75rem 1.25rem;
  text-align: left;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-secondary);
  white-space: nowrap;
}
.pos-row {
  border-bottom: 1px solid var(--surface-border);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.pos-row:hover { background: var(--surface-2); }
.pos-row:last-child { border-bottom: none; }
.pos-table td { padding: 0.9rem 1.25rem; vertical-align: middle; font-size: 0.875rem; color: var(--text-secondary); }

.sym-cell { display: flex; align-items: center; gap: 0.6rem; }
.sym-badge {
  width: 30px; height: 30px;
  background: linear-gradient(135deg, var(--surface-3), var(--surface-2));
  border: 1px solid var(--surface-border-strong);
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 900; color: var(--bip-gold);
  flex-shrink: 0;
}
.sym-text { font-weight: 700; font-size: 0.9rem; color: var(--text-primary); }
.qty-cell { color: var(--text-primary); font-weight: 600; }
.reserved-tag {
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
  background: rgba(100,116,139,0.1);
  border: 1px solid rgba(100,116,139,0.2);
  border-radius: 99px;
  padding: 0.1rem 0.5rem;
}
.fw-bold { font-weight: 700; color: var(--text-primary) !important; }
.pl-cell { font-size: 0.82rem; font-weight: 700; }
.text-muted { color: var(--text-muted); }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem;
  text-align: center;
  color: var(--text-muted);
}
.empty-state .pi { font-size: 2.5rem; }
.empty-state p { font-size: 0.9rem; }

/* Skeleton */
.loading-rows { display: flex; flex-direction: column; }
.skeleton-row {
  display: flex; align-items: center; gap: 1rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--surface-border);
}
.skel { height: 12px; border-radius: 6px; background: var(--surface-2); animation: pulse 1.5s ease infinite alternate; }
.skel-sm { width: 60px; }
.skel-md { width: 100px; }
.skel-lg { flex: 1; }
@keyframes pulse { from { opacity: 0.5; } to { opacity: 1; } }
</style>
