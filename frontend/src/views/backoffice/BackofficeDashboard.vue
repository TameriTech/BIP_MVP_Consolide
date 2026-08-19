<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { adminApi } from "@/api/admin";
import { kycApi } from "@/api/kyc";
import { ordersApi } from "@/api/orders";

const router = useRouter();
const pendingKyc = ref(0);
const totalUsers = ref(0);
const totalOrders = ref(0);
const executedOrders = ref(0);
const rejectedOrders = ref(0);
const loading = ref(true);

onMounted(async () => {
  loading.value = true;
  try {
    const [kyc, users, orders] = await Promise.all([
      kycApi.list("submitted"),
      adminApi.listUsers(),
      ordersApi.listAllBackoffice(),
    ]);
    pendingKyc.value    = kyc.length;
    totalUsers.value    = users.length;
    totalOrders.value   = orders.length;
    executedOrders.value = orders.filter((o) => o.status === "executed").length;
    rejectedOrders.value = orders.filter((o) => o.status === "rejected").length;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page animate-fade-in">
    <div class="page-header">
      <div>
        <h1>Back-office</h1>
        <p class="sub">Administration dashboard — BIP simulation platform</p>
      </div>
      <div class="staff-badge">
        <i class="pi pi-shield"></i>
        Staff access
      </div>
    </div>

    <!-- Metric cards -->
    <div class="metrics-grid">
      <div
        class="metric-card animate-fade-up stagger-1"
        :class="pendingKyc > 0 ? 'metric-urgent' : ''"
        @click="router.push({ name: 'backoffice-kyc' })"
      >
        <div class="metric-icon" :class="pendingKyc > 0 ? 'icon-warn' : 'icon-neutral'">
          <i class="pi pi-id-card"></i>
        </div>
        <div class="metric-body">
          <div class="metric-label">Pending KYC Reviews</div>
          <div class="metric-value" :class="pendingKyc > 0 ? 'value-warn' : ''">{{ pendingKyc }}</div>
        </div>
        <i class="pi pi-chevron-right metric-arrow"></i>
      </div>

      <div class="metric-card animate-fade-up stagger-2" @click="router.push({ name: 'backoffice-users' })">
        <div class="metric-icon icon-blue"><i class="pi pi-users"></i></div>
        <div class="metric-body">
          <div class="metric-label">Total Users</div>
          <div class="metric-value">{{ totalUsers }}</div>
        </div>
        <i class="pi pi-chevron-right metric-arrow"></i>
      </div>

      <div class="metric-card animate-fade-up stagger-3" @click="router.push({ name: 'backoffice-orders' })">
        <div class="metric-icon icon-purple"><i class="pi pi-list"></i></div>
        <div class="metric-body">
          <div class="metric-label">Total Orders</div>
          <div class="metric-value">{{ totalOrders }}</div>
        </div>
        <i class="pi pi-chevron-right metric-arrow"></i>
      </div>

      <div class="metric-card animate-fade-up stagger-4" @click="router.push({ name: 'backoffice-orders' })">
        <div class="metric-icon icon-green"><i class="pi pi-check-circle"></i></div>
        <div class="metric-body">
          <div class="metric-label">Executed Orders</div>
          <div class="metric-value value-green">{{ executedOrders }}</div>
        </div>
        <i class="pi pi-chevron-right metric-arrow"></i>
      </div>

      <div class="metric-card animate-fade-up stagger-5" @click="router.push({ name: 'backoffice-orders' })">
        <div class="metric-icon icon-red"><i class="pi pi-times-circle"></i></div>
        <div class="metric-body">
          <div class="metric-label">Rejected Orders</div>
          <div class="metric-value value-red">{{ rejectedOrders }}</div>
        </div>
        <i class="pi pi-chevron-right metric-arrow"></i>
      </div>
    </div>

    <!-- Quick nav shortcuts -->
    <div class="shortcuts-panel animate-fade-up">
      <div class="panel-header"><h2>Quick access</h2></div>
      <div class="shortcuts-grid">
        <button class="shortcut" @click="router.push({ name: 'backoffice-kyc' })">
          <div class="sc-icon sc-orange"><i class="pi pi-id-card"></i></div>
          <div>
            <div class="sc-title">KYC Queue</div>
            <div class="sc-sub">Review submitted files</div>
          </div>
        </button>
        <button class="shortcut" @click="router.push({ name: 'backoffice-users' })">
          <div class="sc-icon sc-blue"><i class="pi pi-users"></i></div>
          <div>
            <div class="sc-title">User Management</div>
            <div class="sc-sub">Activate, suspend accounts</div>
          </div>
        </button>
        <button class="shortcut" @click="router.push({ name: 'backoffice-instruments' })">
          <div class="sc-icon sc-teal"><i class="pi pi-chart-bar"></i></div>
          <div>
            <div class="sc-title">Instruments</div>
            <div class="sc-sub">Manage market listings</div>
          </div>
        </button>
        <button class="shortcut" @click="router.push({ name: 'backoffice-audit-log' })">
          <div class="sc-icon sc-purple"><i class="pi pi-eye"></i></div>
          <div>
            <div class="sc-title">Audit Log</div>
            <div class="sc-sub">Track all sensitive actions</div>
          </div>
        </button>
        <button class="shortcut" @click="router.push({ name: 'backoffice-ledger' })">
          <div class="sc-icon sc-gold"><i class="pi pi-book"></i></div>
          <div>
            <div class="sc-title">Platform Ledger</div>
            <div class="sc-sub">All transaction records</div>
          </div>
        </button>
        <button class="shortcut" @click="router.push({ name: 'backoffice-settings' })">
          <div class="sc-icon sc-grey"><i class="pi pi-sliders-h"></i></div>
          <div>
            <div class="sc-title">Settings</div>
            <div class="sc-sub">Platform configuration</div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 1.75rem; }
.sub { font-size: var(--text-sm); color: var(--text-muted); margin-top: 0.25rem; }

.staff-badge {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: var(--text-xs); font-weight: 700;
  color: #818cf8;
  background: rgba(99,102,241,0.1);
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 99px;
  padding: 0.35rem 0.875rem;
}

/* Metrics */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}
.metric-card {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  display: flex; align-items: center; gap: 1rem;
  cursor: pointer;
  box-shadow: var(--shadow-card);
  transition: all var(--transition-med);
}
.metric-card:hover { background: var(--surface-2); transform: translateY(-2px); border-color: var(--surface-border-strong); }
.metric-urgent { border-color: rgba(245,158,11,0.3) !important; background: rgba(245,158,11,0.04) !important; }

.metric-icon {
  width: 44px; height: 44px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; flex-shrink: 0;
}
.icon-warn    { background: rgba(245,158,11,0.12); color: #fbbf24; }
.icon-neutral { background: rgba(100,116,139,0.12); color: #94a3b8; }
.icon-blue    { background: rgba(59,130,246,0.12);  color: var(--bip-blue); }
.icon-purple  { background: rgba(99,102,241,0.12);  color: #818cf8; }
.icon-green   { background: rgba(16,185,129,0.12);  color: var(--bip-green); }
.icon-red     { background: rgba(239,68,68,0.12);   color: var(--bip-red); }

.metric-body { flex: 1; }
.metric-label { font-size: var(--text-xs); font-weight: 700; letter-spacing: var(--tracking-label); text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.35rem; }
.metric-value { font-size: var(--text-xl); font-weight: 800; letter-spacing: var(--tracking-tight); color: var(--text-primary); line-height: 1.1; font-family: 'JetBrains Mono', monospace; }
.value-warn  { color: #fbbf24; }
.value-green { color: var(--bip-green); }
.value-red   { color: var(--bip-red); }
.metric-arrow { color: var(--text-muted); font-size: var(--text-sm); flex-shrink: 0; }

/* Shortcuts */
.shortcuts-panel {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.panel-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--surface-border);
}
.panel-header h2 {
  font-size: var(--text-xs); font-weight: 700;
  letter-spacing: var(--tracking-label); text-transform: uppercase;
  color: var(--text-secondary); margin: 0;
}
.shortcuts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0;
}
.shortcut {
  display: flex; align-items: center; gap: 1rem;
  padding: 1.25rem 1.5rem;
  background: none; border: none;
  border-bottom: 1px solid var(--surface-border);
  border-right: 1px solid var(--surface-border);
  cursor: pointer;
  text-align: left;
  transition: background var(--transition-fast);
}
.shortcut:hover { background: var(--surface-2); }
.shortcut:nth-child(2n) { border-right: none; }
.shortcut:nth-last-child(-n+2) { border-bottom: none; }
.sc-icon {
  width: 38px; height: 38px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; flex-shrink: 0;
}
.sc-orange { background: rgba(245,158,11,0.12); color: #fbbf24; }
.sc-blue   { background: rgba(59,130,246,0.12);  color: var(--bip-blue); }
.sc-teal   { background: rgba(20,184,166,0.12);  color: #2dd4bf; }
.sc-purple { background: rgba(99,102,241,0.12);  color: #818cf8; }
.sc-gold   { background: rgba(240,180,41,0.12);  color: var(--bip-gold); }
.sc-grey   { background: rgba(100,116,139,0.12); color: #94a3b8; }
.sc-title  { font-size: var(--text-sm); font-weight: 700; color: var(--text-primary); }
.sc-sub    { font-size: var(--text-xs); color: var(--text-muted); margin-top: 2px; }
</style>
