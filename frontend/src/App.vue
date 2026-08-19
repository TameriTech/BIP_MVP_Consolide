<script setup lang="ts">
import ConfirmDialog from "primevue/confirmdialog";
import Toast from "primevue/toast";
import { computed } from "vue";
import { useRoute } from "vue-router";

import AppShell from "@/layouts/AppShell.vue";

const route = useRoute();
const isBare = computed(() => route.meta.public === true);
</script>

<template>
  <Toast />
  <ConfirmDialog />
  <router-view v-if="isBare" />
  <AppShell v-else />
</template>
