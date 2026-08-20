<script setup lang="ts">
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { authApi } from "@/api/auth";
import { errorMessage } from "@/api/http";

const route = useRoute();
const router = useRouter();

const token = ref(String(route.query.token ?? ""));
const newPassword = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const error = ref("");
const done = ref(false);

async function submit() {
  error.value = "";
  if (newPassword.value !== confirmPassword.value) {
    error.value = "Passwords do not match.";
    return;
  }
  loading.value = true;
  try {
    await authApi.resetPassword({ token: token.value, new_password: newPassword.value });
    done.value = true;
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="bg-grid" aria-hidden="true"></div>
    <div class="bg-glow" aria-hidden="true"></div>

    <div class="auth-card animate-fade-up">
      <div class="auth-logo">
        <div class="brand-mark logo-icon">B</div>
        <div class="logo-text">
          <span class="logo-name">BIP</span>
          <span class="logo-sub">Bourse d'Investissement Participatif</span>
        </div>
      </div>

      <div class="auth-divider"></div>

      <template v-if="!done">
        <div class="auth-header">
          <h1>Choose a new password</h1>
          <p>Set a new password for your account.</p>
        </div>

        <form class="auth-form" @submit.prevent="submit">
          <div class="field">
            <label for="token">Reset token</label>
            <InputText id="token" v-model="token" placeholder="Paste your reset token" required fluid />
          </div>

          <div class="field">
            <label for="new-password">New password</label>
            <Password
              id="new-password"
              v-model="newPassword"
              toggle-mask
              required
              fluid
              placeholder="Min. 8 characters"
            />
          </div>

          <div class="field">
            <label for="confirm-password">Confirm new password</label>
            <Password
              id="confirm-password"
              v-model="confirmPassword"
              :feedback="false"
              toggle-mask
              required
              fluid
              placeholder="Re-enter new password"
            />
          </div>

          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

          <Button type="submit" label="Reset password" :loading="loading" fluid class="submit-btn" />
        </form>
      </template>

      <template v-else>
        <div class="auth-header">
          <h1>Password updated</h1>
          <p>Your password has been reset. You can now sign in with your new password.</p>
        </div>
        <Button label="Go to sign in" fluid class="submit-btn" @click="router.push({ name: 'login' })" />
      </template>

      <p v-if="!done" class="auth-switch">
        Remembered it?
        <router-link to="/login">Back to sign in</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-0);
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
}
.bg-glow {
  position: absolute;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 400px;
  background: radial-gradient(ellipse at center, rgba(240,180,41,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.auth-card {
  width: 100%;
  max-width: 420px;
  background: linear-gradient(145deg, var(--surface-1) 0%, var(--surface-2) 100%);
  border: 1px solid var(--surface-border-strong);
  border-radius: var(--radius-xl);
  padding: 2.25rem;
  box-shadow: 0 25px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04);
  position: relative;
  z-index: 1;
}
.auth-logo { display: flex; align-items: center; gap: 0.75rem; }
.logo-icon { width: 44px; height: 44px; font-size: 1.35rem; }
.logo-text { display: flex; flex-direction: column; }
.logo-name {
  font-size: var(--text-lg);
  font-weight: 800;
  letter-spacing: var(--tracking-tight);
  color: var(--text-primary);
  line-height: 1.1;
}
.logo-sub { font-size: var(--text-2xs); color: var(--text-muted); margin-top: 3px; }
.auth-divider { height: 1px; background: var(--surface-border); margin: 1.5rem 0; }
.auth-header { margin-bottom: 1.5rem; }
.auth-header h1 {
  font-size: var(--text-xl);
  font-weight: 800;
  letter-spacing: var(--tracking-tight);
  color: var(--text-primary);
  margin-bottom: 0.3rem;
}
.auth-header p { font-size: var(--text-sm); color: var(--text-secondary); }
.auth-form { display: flex; flex-direction: column; gap: 1.1rem; }
.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field label { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); }
.submit-btn { margin-top: 0.25rem; }
.auth-switch {
  margin-top: 1.25rem;
  text-align: center;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
</style>
