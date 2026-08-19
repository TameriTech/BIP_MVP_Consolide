import { createRouter, createWebHistory } from "vue-router";

import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/auth/Login.vue"),
      meta: { public: true },
    },
    {
      path: "/register",
      name: "register",
      component: () => import("@/views/auth/Register.vue"),
      meta: { public: true },
    },
    {
      path: "/onboarding/kyc",
      name: "onboarding-kyc",
      component: () => import("@/views/onboarding/Kyc.vue"),
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("@/views/Dashboard.vue"),
    },
    {
      path: "/market",
      name: "market-list",
      component: () => import("@/views/market/MarketList.vue"),
    },
    {
      path: "/market/:symbol",
      name: "market-detail",
      component: () => import("@/views/market/MarketDetail.vue"),
      props: true,
    },
    {
      path: "/orders",
      name: "order-history",
      component: () => import("@/views/orders/OrderHistory.vue"),
    },
    {
      path: "/orders/:id",
      name: "order-detail",
      component: () => import("@/views/orders/OrderDetail.vue"),
      props: true,
    },
    {
      path: "/portfolio",
      name: "portfolio",
      component: () => import("@/views/portfolio/Portfolio.vue"),
    },
    {
      path: "/ledger",
      name: "ledger",
      component: () => import("@/views/ledger/Ledger.vue"),
    },
    {
      path: "/account/settings",
      name: "account-settings",
      component: () => import("@/views/AccountSettings.vue"),
    },
    {
      path: "/backoffice",
      name: "backoffice-dashboard",
      component: () => import("@/views/backoffice/BackofficeDashboard.vue"),
      meta: { staffOnly: true },
    },
    {
      path: "/backoffice/kyc",
      name: "backoffice-kyc",
      component: () => import("@/views/backoffice/KycQueue.vue"),
      meta: { staffOnly: true },
    },
    {
      path: "/backoffice/users",
      name: "backoffice-users",
      component: () => import("@/views/backoffice/Users.vue"),
      meta: { staffOnly: true },
    },
    {
      path: "/backoffice/instruments",
      name: "backoffice-instruments",
      component: () => import("@/views/backoffice/Instruments.vue"),
      meta: { staffOnly: true },
    },
    {
      path: "/backoffice/orders",
      name: "backoffice-orders",
      component: () => import("@/views/backoffice/Orders.vue"),
      meta: { staffOnly: true },
    },
    {
      path: "/backoffice/ledger",
      name: "backoffice-ledger",
      component: () => import("@/views/backoffice/Ledger.vue"),
      meta: { staffOnly: true },
    },
    {
      path: "/backoffice/audit-log",
      name: "backoffice-audit-log",
      component: () => import("@/views/backoffice/AuditLog.vue"),
      meta: { staffOnly: true },
    },
    {
      path: "/backoffice/settings",
      name: "backoffice-settings",
      component: () => import("@/views/backoffice/Settings.vue"),
      meta: { staffOnly: true },
    },
  ],
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!auth.initialized) {
    await auth.fetchMe();
  }

  if (to.meta.public) {
    if (auth.isAuthenticated && (to.name === "login" || to.name === "register")) {
      return { name: auth.isStaff ? "backoffice-dashboard" : "dashboard" };
    }
    return true;
  }

  if (!auth.isAuthenticated) {
    return { name: "login" };
  }

  // Staff accounts are never KYC-validated (they don't trade), so the investor
  // dashboard's "complete KYC" prompt makes no sense for them — route every
  // path that resolves to the investor dashboard (root redirect, explicit
  // pushes to "dashboard" from anywhere) to their own dashboard instead.
  if (to.name === "dashboard" && auth.isStaff) {
    return { name: "backoffice-dashboard" };
  }

  if (to.meta.staffOnly && !auth.isStaff) {
    return { name: "dashboard" };
  }

  return true;
});

export default router;
