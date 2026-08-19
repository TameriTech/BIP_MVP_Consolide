import { defineStore } from "pinia";
import { ref } from "vue";

import { marketApi } from "@/api/market";
import type { Instrument } from "@/api/types";

export const useMarketStore = defineStore("market", () => {
  const instruments = ref<Instrument[]>([]);
  const loading = ref(false);

  async function fetchAll() {
    loading.value = true;
    try {
      instruments.value = await marketApi.list();
    } finally {
      loading.value = false;
    }
  }

  return { instruments, loading, fetchAll };
});
