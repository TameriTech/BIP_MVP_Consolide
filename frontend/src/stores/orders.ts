import { defineStore } from "pinia";
import { ref } from "vue";

import { ordersApi } from "@/api/orders";
import type { Order } from "@/api/types";

export const useOrdersStore = defineStore("orders", () => {
  const orders = ref<Order[]>([]);
  const loading = ref(false);

  async function fetchMine() {
    loading.value = true;
    try {
      orders.value = await ordersApi.list();
    } finally {
      loading.value = false;
    }
  }

  return { orders, loading, fetchMine };
});
