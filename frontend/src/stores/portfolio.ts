import { defineStore } from "pinia";
import { ref } from "vue";

import { portfolioApi } from "@/api/portfolio";
import type { Performance, Portfolio } from "@/api/types";

export const usePortfolioStore = defineStore("portfolio", () => {
  const portfolio = ref<Portfolio | null>(null);
  const performance = ref<Performance | null>(null);
  const loading = ref(false);

  async function fetch() {
    loading.value = true;
    try {
      portfolio.value = await portfolioApi.getMine();
    } finally {
      loading.value = false;
    }
  }

  async function fetchPerformance() {
    performance.value = await portfolioApi.getMyPerformance();
  }

  return { portfolio, performance, loading, fetch, fetchPerformance };
});
