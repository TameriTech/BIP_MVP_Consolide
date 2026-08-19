<script setup lang="ts">
import Button from "primevue/button";
import Message from "primevue/message";
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";
import { useKycStore } from "@/stores/kyc";
import { useOrdersStore } from "@/stores/orders";
import { usePortfolioStore } from "@/stores/portfolio";

const auth = useAuthStore();
const kyc = useKycStore();
const portfolio = usePortfolioStore();
const orders = useOrdersStore();
const router = useRouter();

onMounted(async () => {
  await kyc.fetchMine();
  if (kyc.current?.status === "validated") {
    await Promise.all([portfolio.fetch(), portfolio.fetchPerformance(), orders.fetchMine()]);
  }
});

function fmt(val: string | undefined) {
  if (!val) return "—";
  return Number(val).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDiff(val: string | undefined) {
  if (!val) return "";
  const n = Number(val);
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

const recentOrders = () => (orders.orders ?? []).slice(0, 5);

const statusSeverity: Record<string, string> = {
  executed: "success", rejected: "danger", cancelled: "secondary",
  reserved: "info", submitted: "info",
};

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}
</script>

<template>
  <div class="dashboard animate-fade-in">
    <!-- Page header -->
    <div class="page-header">
      <div>
        <p class="greeting-sub">Good day</p>
        <h1>{{ auth.user?.full_name }}</h1>
      </div>
      <div class="header-actions">
        <Button
          label="Browse market"
          icon="pi pi-chart-line"
          @click="router.push({ name: 'market-list' })"
        />
      </div>
    </div>

    <!-- KYC warning -->
    <Message
      v-if="kyc.current && kyc.current.status !== 'validated'"
      severity="warn"
      :closable="false"
      class="kyc-warn animate-fade-up"
    >
      <div class="kyc-message">
        <div>
          <strong>Account not yet active.</strong>
          Complete your identity verification to start trading on the demo market.
        </div>
        <Button
          label="Verify identity"
          size="small"
          @click="router.push({ name: 'onboarding-kyc' })"
        />
      </div>
    </Message>

    <!-- Stat cards -->
    <div v-if="portfolio.portfolio" class="stats-grid">
      <div class="stat-card animate-fade-up stagger-1">
        <div class="stat-icon stat-icon-cash"><i class="pi pi-wallet"></i></div>
        <div class="stat-body">
          <div class="stat-label">Cash Available</div>
          <div class="stat-value num">{{ fmt(portfolio.portfolio.cash_available) }} <span class="currency">XOF</span></div>
        </div>
      </div>

      <div class="stat-card animate-fade-up stagger-2">
        <div class="stat-icon stat-icon-portfolio"><i class="pi pi-briefcase"></i></div>
        <div class="stat-body">
          <div class="stat-label">Total Portfolio Value</div>
          <div class="stat-value num">{{ fmt(portfolio.portfolio.total_value) }} <span class="currency">XOF</span></div>
        </div>
      </div>

      <div class="stat-card animate-fade-up stagger-3">
        <div class="stat-icon stat-icon-positions"><i class="pi pi-chart-bar"></i></div>
        <div class="stat-body">
          <div class="stat-label">Open Positions</div>
          <div class="stat-value num">{{ portfolio.portfolio.positions.length }}</div>
        </div>
      </div>

      <div v-if="portfolio.performance" class="stat-card animate-fade-up stagger-4" :class="Number(portfolio.performance.unrealized_pl) >= 0 ? 'stat-pos' : 'stat-neg'">
        <div class="stat-icon" :class="Number(portfolio.performance.unrealized_pl) >= 0 ? 'stat-icon-pos' : 'stat-icon-neg'">
          <i :class="Number(portfolio.performance.unrealized_pl) >= 0 ? 'pi pi-arrow-up-right' : 'pi pi-arrow-down-right'"></i>
        </div>
        <div class="stat-body">
          <div class="stat-label">Unrealized P&amp;L</div>
          <div class="stat-value num" :class="Number(portfolio.performance.unrealized_pl) >= 0 ? 'pos' : 'neg'">
            {{ Number(portfolio.performance.unrealized_pl) >= 0 ? "+" : "" }}{{ fmt(portfolio.performance.unrealized_pl) }}
            <span class="pct-badge" :class="Number(portfolio.performance.unrealized_pl) >= 0 ? 'pct-pos' : 'pct-neg'">
              {{ fmtDiff(portfolio.performance.unrealized_pl_pct) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Two-column lower area -->
    <div class="lower-grid" v-if="portfolio.portfolio">
      <!-- Recent orders -->
      <div class="panel animate-fade-up stagger-2">
        <div class="panel-header">
          <h2>Recent Orders</h2>
          <button class="panel-link" @click="router.push({ name: 'order-history' })">
            View all <i class="pi pi-arrow-right"></i>
          </button>
        </div>

        <div v-if="recentOrders().length" class="orders-list">
          <div
            v-for="order in recentOrders()"
            :key="order.id"
            class="order-row"
            @click="router.push({ name: 'order-detail', params: { id: order.id } })"
          >
            <div class="order-side-badge" :class="order.side === 'buy' ? 'side-buy' : 'side-sell'">
              {{ order.side.toUpperCase() }}
            </div>
            <div class="order-info">
              <div class="order-qty">{{ order.quantity }} units</div>
              <div class="order-time">{{ timeAgo(order.created_at) }}</div>
            </div>
            <div class="order-amount num">
              {{ order.estimated_amount ? `${fmt(order.estimated_amount)} XOF` : "—" }}
            </div>
            <div class="order-status-dot" :class="`dot-${statusSeverity[order.status] ?? 'secondary'}`"></div>
          </div>
        </div>

        <div v-else class="panel-empty">
          <i class="pi pi-inbox"></i>
          <p>No orders yet. Head to the market to place your first trade.</p>
          <Button label="Go to market" size="small" severity="secondary" @click="router.push({ name: 'market-list' })" />
        </div>
      </div>

      <!-- Quick actions -->
      <div class="panel animate-fade-up stagger-3">
        <div class="panel-header"><h2>Quick actions</h2></div>
        <div class="quick-actions">
          <button class="qa-btn" @click="router.push({ name: 'market-list' })">
            <div class="qa-icon qa-blue"><i class="pi pi-chart-line"></i></div>
            <span class="qa-label">Browse Market</span>
            <i class="pi pi-chevron-right qa-arrow"></i>
          </button>
          <button class="qa-btn" @click="router.push({ name: 'portfolio' })">
            <div class="qa-icon qa-purple"><i class="pi pi-briefcase"></i></div>
            <span class="qa-label">View Portfolio</span>
            <i class="pi pi-chevron-right qa-arrow"></i>
          </button>
          <button class="qa-btn" @click="router.push({ name: 'order-history' })">
            <div class="qa-icon qa-gold"><i class="pi pi-list"></i></div>
            <span class="qa-label">Order History</span>
            <i class="pi pi-chevron-right qa-arrow"></i>
          </button>
          <button class="qa-btn" @click="router.push({ name: 'ledger' })">
            <div class="qa-icon qa-teal"><i class="pi pi-book"></i></div>
            <span class="qa-label">Transaction Ledger</span>
            <i class="pi pi-chevron-right qa-arrow"></i>
          </button>
        </div>

        <!-- Simulation disclaimer -->
        <div class="disclaimer-box">
          <div class="disclaimer-dot"><span class="live-dot"></span></div>
          <div class="disclaimer-text">
            <strong>Simulation active</strong>
            All prices, orders, and balances are virtual. No real money is involved.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

/* Header */
.greeting-sub {
  font-size: 0.78rem;
  color: var(--text-muted);
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-bottom: 0.2rem;
}
.header-actions { display: flex; gap: 0.75rem; }

/* KYC warn */
.kyc-warn { animation: fadeUp 0.4s ease both; }
.kyc-message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: linear-gradient(135deg, var(--surface-1) 0%, var(--surface-2) 100%);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: var(--shadow-card);
  transition: border-color var(--transition-med), transform var(--transition-fast);
  cursor: default;
}
.stat-card:hover { border-color: var(--surface-border-strong); transform: translateY(-2px); }
.stat-card.stat-pos { border-color: rgba(16,185,129,0.25); }
.stat-card.stat-neg { border-color: rgba(239,68,68,0.2); }

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;
}
.stat-icon-cash     { background: rgba(240,180,41,0.12);  color: var(--bip-gold); }
.stat-icon-portfolio{ background: rgba(99,102,241,0.12);  color: #818cf8; }
.stat-icon-positions{ background: rgba(59,130,246,0.12);  color: var(--bip-blue); }
.stat-icon-pos      { background: rgba(16,185,129,0.12);  color: var(--bip-green); }
.stat-icon-neg      { background: rgba(239,68,68,0.12);   color: var(--bip-red); }

.stat-body { min-width: 0; }
.stat-label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 0.35rem;
}
.stat-value {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.1;
  color: var(--text-primary);
}
.currency {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  font-family: 'Inter', sans-serif;
}
.pct-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 99px;
  margin-left: 0.35rem;
  font-family: 'Inter', sans-serif;
  letter-spacing: 0.03em;
}
.pct-pos { background: rgba(16,185,129,0.15); color: var(--bip-green); }
.pct-neg { background: rgba(239,68,68,0.15);  color: var(--bip-red); }

/* Lower two-column grid */
.lower-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 1.25rem;
}
@media (max-width: 960px) { .lower-grid { grid-template-columns: 1fr; } }

/* Panel */
.panel {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-card);
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}
.panel-header h2 {
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-secondary);
}
.panel-link {
  background: none;
  border: none;
  color: var(--bip-gold);
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-family: 'Inter', sans-serif;
  transition: color var(--transition-fast);
}
.panel-link:hover { color: var(--bip-gold-light); }

/* Orders list */
.orders-list { display: flex; flex-direction: column; gap: 0.5rem; }
.order-row {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.75rem;
  background: var(--surface-2);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}
.order-row:hover { background: var(--surface-3); border-color: var(--surface-border-strong); }
.order-side-badge {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  padding: 0.2rem 0.55rem;
  border-radius: 99px;
  flex-shrink: 0;
}
.side-buy  { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
.side-sell { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.order-info { flex: 1; min-width: 0; }
.order-qty  { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
.order-time { font-size: 0.72rem; color: var(--text-muted); margin-top: 1px; }
.order-amount {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-align: right;
}
.order-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-success   { background: var(--bip-green); }
.dot-danger    { background: var(--bip-red); }
.dot-info      { background: var(--bip-blue); }
.dot-secondary { background: var(--text-muted); }

.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem 0;
  text-align: center;
  color: var(--text-muted);
}
.panel-empty .pi { font-size: 2rem; }
.panel-empty p { font-size: 0.85rem; max-width: 240px; }

/* Quick actions */
.quick-actions { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.25rem; }
.qa-btn {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem;
  background: var(--surface-2);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
  font-family: 'Inter', sans-serif;
  text-align: left;
  width: 100%;
}
.qa-btn:hover { background: var(--surface-3); border-color: var(--surface-border-strong); }
.qa-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}
.qa-blue   { background: rgba(59,130,246,0.12);  color: var(--bip-blue); }
.qa-purple { background: rgba(99,102,241,0.12);  color: #818cf8; }
.qa-gold   { background: rgba(240,180,41,0.12);  color: var(--bip-gold); }
.qa-teal   { background: rgba(20,184,166,0.12);  color: #2dd4bf; }
.qa-label  { flex: 1; font-size: 0.875rem; font-weight: 600; color: var(--text-primary); }
.qa-arrow  { color: var(--text-muted); font-size: 0.8rem; }

/* Disclaimer */
.disclaimer-box {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  background: rgba(16,185,129,0.06);
  border: 1px solid rgba(16,185,129,0.15);
  border-radius: var(--radius-md);
  padding: 0.875rem;
}
.disclaimer-dot { padding-top: 2px; }
.disclaimer-text {
  font-size: 0.78rem;
  color: var(--text-secondary);
  line-height: 1.5;
}
.disclaimer-text strong { display: block; color: var(--bip-green); margin-bottom: 2px; }
</style>
