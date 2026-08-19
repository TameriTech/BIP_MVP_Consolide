import { defineStore } from "pinia";
import { ref } from "vue";

import { kycApi } from "@/api/kyc";
import type { KycFile } from "@/api/types";

export const useKycStore = defineStore("kyc", () => {
  const current = ref<KycFile | null>(null);
  const loading = ref(false);

  async function fetchMine() {
    loading.value = true;
    try {
      current.value = await kycApi.getMine();
    } finally {
      loading.value = false;
    }
  }

  async function saveDraft(data: Partial<KycFile>) {
    current.value = await kycApi.upsertMine(data);
  }

  async function submit() {
    current.value = await kycApi.submitMine();
  }

  return { current, loading, fetchMine, saveDraft, submit };
});
