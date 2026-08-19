<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const sidebarOpen = ref(true);

const investorNav = [
  { label: "Dashboard",  icon: "pi-th-large",     name: "dashboard" },
  { label: "Market",     icon: "pi-chart-line",   name: "market-list" },
  { label: "Orders",     icon: "pi-list",         name: "order-history" },
  { label: "Portfolio",  icon: "pi-briefcase",    name: "portfolio" },
  { label: "Ledger",     icon: "pi-book",         name: "ledger" },
  { label: "Settings",   icon: "pi-cog",          name: "account-settings" },
];

const staffNav = [
  { label: "Dashboard",   icon: "pi-th-large",   name: "backoffice-dashboard" },
  { label: "KYC Queue",   icon: "pi-id-card",    name: "backoffice-kyc" },
  { label: "Users",       icon: "pi-users",       name: "backoffice-users" },
  { label: "Instruments", icon: "pi-chart-bar",  name: "backoffice-instruments" },
  { label: "Orders",      icon: "pi-list",        name: "backoffice-orders" },
  { label: "Ledger",      icon: "pi-book",        name: "backoffice-ledger" },
  { label: "Audit Log",   icon: "pi-eye",         name: "backoffice-audit-log" },
  { label: "Settings",    icon: "pi-sliders-h",   name: "backoffice-settings" },
];

const navItems = computed(() => (auth.isStaff ? staffNav : investorNav));

function isActive(name: string) {
  return route.name === name;
}

function go(name: string) {
  router.push({ name });
}

function doLogout() {
  auth.logout();
  router.push({ name: "login" });
}

const initials = computed(() => {
  const name = auth.user?.full_name ?? "";
  return name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase();
});

const roleLabel = computed(() => {
  const r = auth.user?.role ?? "";
  return { investor: "Investor", admin: "Admin", backoffice_operator: "Operator", super_admin: "Super Admin" }[r] ?? r;
});
</script>

<template>
  <div class="shell" :class="{ 'sidebar-collapsed': !sidebarOpen }">
    <!-- ── Sidebar ── -->
    <aside class="sidebar">
      <!-- Brand -->
      <div class="brand" @click="go(auth.isStaff ? 'backoffice-dashboard' : 'dashboard')">
        <div class="brand-logo">
          <span class="brand-icon">₿</span>
        </div>
        <div class="brand-text">
          <span class="brand-name">BIP</span>
          <span class="brand-sub">Bourse d'Investissement</span>
        </div>
      </div>

      <!-- Simulation badge -->
      <div class="sim-badge">
        <span class="live-dot"></span>
        <span>Simulation active</span>
      </div>

      <!-- Nav -->
      <nav class="nav">
        <button
          v-for="item in navItems"
          :key="item.name"
          class="nav-item"
          :class="{ active: isActive(item.name) }"
          @click="go(item.name)"
        >
          <i :class="`pi ${item.icon} nav-icon`"></i>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="isActive(item.name)" class="nav-active-bar"></span>
        </button>
      </nav>

      <!-- Spacer -->
      <div class="sidebar-spacer"></div>

      <!-- User card -->
      <div class="user-card">
        <div class="user-avatar">{{ initials }}</div>
        <div class="user-info">
          <div class="user-name">{{ auth.user?.full_name }}</div>
          <div class="user-role">{{ roleLabel }}</div>
        </div>
        <button class="logout-btn" title="Log out" @click="doLogout">
          <i class="pi pi-sign-out"></i>
        </button>
      </div>
    </aside>

    <!-- ── Main area ── -->
    <div class="main-area">
      <!-- Top bar -->
      <header class="topbar">
        <button class="toggle-btn" @click="sidebarOpen = !sidebarOpen">
          <i class="pi pi-bars"></i>
        </button>
        <div class="topbar-right">
          <div class="sim-pill">
            <span class="live-dot"></span>
            Demo market — no real money
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ── Shell layout ── */
.shell {
  display: flex;
  min-height: 100vh;
  background: var(--surface-0);
}

/* ── Sidebar ── */
.sidebar {
  width: 240px;
  min-width: 240px;
  background: linear-gradient(180deg, var(--surface-1) 0%, #0c1018 100%);
  border-right: 1px solid var(--surface-border);
  display: flex;
  flex-direction: column;
  padding: 1.25rem 0.75rem;
  gap: 0.5rem;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.25s cubic-bezier(0.4,0,0.2,1), min-width 0.25s cubic-bezier(0.4,0,0.2,1);
  z-index: 50;
}
.sidebar-collapsed .sidebar {
  width: 64px;
  min-width: 64px;
}
.sidebar-collapsed .brand-text,
.sidebar-collapsed .brand-sub,
.sidebar-collapsed .sim-badge,
.sidebar-collapsed .nav-label,
.sidebar-collapsed .user-info,
.sidebar-collapsed .nav-active-bar {
  display: none;
}

/* ── Brand ── */
.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.25rem 0.5rem 1rem;
  cursor: pointer;
  user-select: none;
}
.brand-logo {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, #f0b429, #d97706);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(240,180,41,0.35);
}
.brand-icon {
  font-size: 1.3rem;
  color: #1a1000;
  font-weight: 900;
}
.brand-name {
  font-size: 1.2rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}
.brand-sub {
  font-size: 0.62rem;
  color: var(--text-muted);
  letter-spacing: 0.01em;
  margin-top: -2px;
  display: block;
}

/* ── Simulation badge ── */
.sim-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--bip-green);
  background: rgba(16,185,129,0.08);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: 99px;
  padding: 0.3rem 0.75rem;
  margin: 0 0.25rem 0.75rem;
  letter-spacing: 0.03em;
}

/* ── Nav ── */
.nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-size: 0.85rem;
  font-weight: 500;
  text-align: left;
  width: 100%;
  position: relative;
  transition: background var(--transition-fast), color var(--transition-fast);
  white-space: nowrap;
  overflow: hidden;
}
.nav-item:hover {
  background: var(--surface-2);
  color: var(--text-primary);
}
.nav-item.active {
  background: rgba(240,180,41,0.1);
  color: var(--bip-gold);
  font-weight: 600;
}
.nav-icon {
  font-size: 1rem;
  flex-shrink: 0;
  width: 18px;
  text-align: center;
}
.nav-active-bar {
  position: absolute;
  right: 0;
  top: 20%;
  height: 60%;
  width: 3px;
  background: var(--bip-gold);
  border-radius: 99px;
}

/* ── Spacer ── */
.sidebar-spacer { flex: 1; }

/* ── User card ── */
.user-card {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.75rem;
  background: var(--surface-2);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  margin-top: 0.5rem;
}
.user-avatar {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 800;
  color: white;
  flex-shrink: 0;
}
.user-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
.user-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-role {
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-top: 1px;
}
.logout-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: color var(--transition-fast), background var(--transition-fast);
  flex-shrink: 0;
}
.logout-btn:hover { color: var(--bip-red); background: rgba(239,68,68,0.1); }

/* ── Main area ── */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* ── Topbar ── */
.topbar {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  border-bottom: 1px solid var(--surface-border);
  background: rgba(10,13,20,0.7);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 40;
  flex-shrink: 0;
}
.toggle-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 1.1rem;
  padding: 0.35rem;
  border-radius: 6px;
  transition: color var(--transition-fast), background var(--transition-fast);
}
.toggle-btn:hover { color: var(--text-primary); background: var(--surface-2); }
.topbar-right { display: flex; align-items: center; gap: 1rem; }
.sim-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--bip-green);
  background: rgba(16,185,129,0.08);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: 99px;
  padding: 0.3rem 0.75rem;
  letter-spacing: 0.03em;
}

/* ── Page content ── */
.content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 200;
    transform: translateX(0);
  }
  .sidebar-collapsed .sidebar {
    transform: translateX(-100%);
    width: 240px;
    min-width: 240px;
  }
  .content { padding: 1rem; }
}
</style>
