<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { useOrdersStore } from "@/stores/orders";

const orders = useOrdersStore();
const router = useRouter();

onMounted(() => orders.fetchMine());

const statusMap: Record<string, { label: string; cls: string }> = {
  executed:  { label: "Executed",  cls: "status-success" },
  rejected:  { label: "Rejected",  cls: "status-danger"  },
  cancelled: { label: "Cancelled", cls: "status-neutral"  },
  reserved:  { label: "Reserved",  cls: "status-info"    },
  submitted: { label: "Submitted", cls: "status-info"    },
  draft:     { label: "Draft",     cls: "status-neutral"  },
};

function open(id: string) {
  router.push({ name: "order-detail", params: { id } });
}

function fmt(val: string | null) {
  if (!val) return "—";
  return Number(val).toLocaleString("en-US", { minimumFractionDigits: 2 });
}

function fmtDate(d: string) {
  return new Date(d).toLocaleString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}
</script>

<template>
  <div class="page animate-fade-in">
    <div class="page-header">
      <h1>Order History</h1>
      <span class="order-count">{{ orders.orders.length }} orders</span>
    </div>

    <!-- Loading skeleton -->
    <div v-if="orders.loading" class="orders-panel">
      <div v-for="i in 6" :key="i" class="skeleton-row">
        <div class="skel skel-xs"></div>
        <div class="skel skel-lg"></div>
        <div class="skel skel-md"></div>
        <div class="skel skel-md"></div>
        <div class="skel skel-sm"></div>
      </div>
    </div>

    <!-- Orders table -->
    <div v-else-if="orders.orders.length" class="orders-panel">
      <div class="table-scroll">
      <table class="orders-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Side</th>
            <th>Type</th>
            <th class="right-align">Quantity</th>
            <th class="right-align">Estimated (USD)</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="order in orders.orders"
            :key="order.id"
            class="order-row"
            @click="open(order.id)"
          >
            <td class="date-cell">{{ fmtDate(order.created_at) }}</td>
            <td>
              <span class="side-badge" :class="order.side === 'buy' ? 'side-buy' : 'side-sell'">
                <i :class="order.side === 'buy' ? 'pi pi-arrow-up-right' : 'pi pi-arrow-down-right'"></i>
                {{ order.side.toUpperCase() }}
              </span>
            </td>
            <td class="type-cell">
              {{ order.order_type.charAt(0).toUpperCase() + order.order_type.slice(1) }}
              <span v-if="order.limit_price" class="limit-price num"> @ {{ fmt(order.limit_price) }}</span>
            </td>
            <td class="right-align num qty-cell">{{ order.quantity }}</td>
            <td class="right-align num amount-cell">{{ fmt(order.estimated_amount) }}</td>
            <td>
              <span class="status-pill" :class="(statusMap[order.status] ?? statusMap.draft).cls">
                {{ (statusMap[order.status] ?? statusMap.draft).label }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-panel">
      <div class="empty-inner">
        <i class="pi pi-inbox"></i>
        <h3>No orders yet</h3>
        <p>Head to the market to place your first simulated trade.</p>
        <button class="go-btn" @click="router.push({ name: 'market-list' })">
          <i class="pi pi-chart-line"></i> Browse market
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: 1.5rem; }
.order-count {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-muted);
  background: var(--surface-2);
  border: 1px solid var(--surface-border);
  border-radius: 99px;
  padding: 0.2rem 0.65rem;
}

.orders-panel {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.orders-table { width: 100%; min-width: 640px; border-collapse: collapse; }
.orders-table thead tr {
  background: var(--surface-2);
  border-bottom: 1px solid var(--surface-border);
}
.orders-table th {
  padding: 0.875rem 1.25rem;
  text-align: left;
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--text-secondary);
}
.right-align { text-align: right !important; }
.order-row {
  border-bottom: 1px solid var(--surface-border);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.order-row:hover { background: var(--surface-2); }
.order-row:last-child { border-bottom: none; }
.orders-table td { padding: 0.9rem 1.25rem; vertical-align: middle; font-size: var(--text-sm); color: var(--text-secondary); }

.date-cell { font-size: var(--text-xs); color: var(--text-muted); white-space: nowrap; }
.side-badge {
  display: inline-flex; align-items: center; gap: 0.3rem;
  font-size: var(--text-2xs); font-weight: 800; letter-spacing: var(--tracking-label);
  padding: 0.2rem 0.65rem; border-radius: 99px;
}
.side-buy  { background: rgba(16,185,129,0.12); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
.side-sell { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.25); }

.type-cell { color: var(--text-primary); font-weight: 500; }
.limit-price { color: var(--text-muted); font-size: var(--text-xs); }
.qty-cell { font-weight: 700; color: var(--text-primary); font-family: 'JetBrains Mono', monospace; }
.amount-cell { font-weight: 600; color: var(--text-primary); font-family: 'JetBrains Mono', monospace; }

.status-pill {
  display: inline-flex; align-items: center;
  font-size: var(--text-2xs); font-weight: 700; letter-spacing: var(--tracking-label); text-transform: uppercase;
  padding: 0.2rem 0.65rem; border-radius: 99px;
}
.status-success { background: rgba(16,185,129,0.12); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
.status-danger  { background: rgba(239,68,68,0.12);  color: #f87171; border: 1px solid rgba(239,68,68,0.25); }
.status-info    { background: rgba(59,130,246,0.12);  color: #60a5fa; border: 1px solid rgba(59,130,246,0.25); }
.status-neutral { background: rgba(100,116,139,0.1);  color: #94a3b8; border: 1px solid rgba(100,116,139,0.2); }

/* Empty */
.empty-panel {
  background: var(--surface-1);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-lg);
  padding: 4rem 2rem;
  display: flex;
  justify-content: center;
  box-shadow: var(--shadow-card);
}
.empty-inner {
  display: flex; flex-direction: column; align-items: center; gap: 0.75rem; text-align: center;
  color: var(--text-muted);
}
.empty-inner .pi { font-size: 2.75rem; margin-bottom: 0.25rem; }
.empty-inner h3 { font-size: var(--text-md); color: var(--text-primary); }
.empty-inner p { font-size: var(--text-sm); max-width: 280px; }
.go-btn {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.6rem 1.25rem;
  background: var(--surface-2);
  border: 1px solid var(--surface-border-strong);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm); font-weight: 600;
  cursor: pointer;
  margin-top: 0.25rem;
  transition: background var(--transition-fast);
}
.go-btn:hover { background: var(--surface-3); }

/* Skeleton */
.skeleton-row {
  display: flex; align-items: center; gap: 1rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--surface-border);
}
.skel { height: 12px; border-radius: 6px; animation: pulse 1.5s ease infinite alternate; background: var(--surface-2); }
.skel-xs { width: 80px; }
.skel-sm { width: 80px; }
.skel-md { width: 110px; }
.skel-lg { flex: 1; }
@keyframes pulse { from { opacity: 0.5; } to { opacity: 1; } }
</style>
