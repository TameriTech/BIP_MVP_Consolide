<script setup lang="ts">
import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
import Password from "primevue/password";
import { useToast } from "primevue/usetoast";
import { ref } from "vue";

import { authApi } from "@/api/auth";
import { errorMessage } from "@/api/http";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const toast = useToast();

const currentPassword = ref("");
const newPassword = ref("");
const loading = ref(false);
const error = ref("");

async function changePassword() {
  loading.value = true;
  error.value = "";
  try {
    await authApi.changePassword({ current_password: currentPassword.value, new_password: newPassword.value });
    toast.add({ severity: "success", summary: "Password changed", life: 2500 });
    currentPassword.value = "";
    newPassword.value = "";
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <h1>Account settings</h1>

    <Card>
      <template #title>Profile</template>
      <template #content>
        <dl>
          <dt>Name</dt>
          <dd>{{ auth.user?.full_name }}</dd>
          <dt>Email</dt>
          <dd>{{ auth.user?.email }}</dd>
          <dt>Role</dt>
          <dd>{{ auth.user?.role }}</dd>
        </dl>
      </template>
    </Card>

    <Card>
      <template #title>Change password</template>
      <template #content>
        <form class="form" @submit.prevent="changePassword">
          <label>
            Current password
            <Password v-model="currentPassword" :feedback="false" toggle-mask required fluid />
          </label>
          <label>
            New password
            <Password v-model="newPassword" toggle-mask required fluid />
          </label>
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
          <Button type="submit" label="Update password" :loading="loading" />
        </form>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 480px;
}
dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1rem;
  margin: 0;
}
dt {
  font-weight: 600;
  color: var(--p-text-muted-color);
}
dd {
  margin: 0;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
  font-size: 0.9rem;
}
</style>
