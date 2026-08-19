<script setup lang="ts">
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";
import { ref } from "vue";
import { useRouter } from "vue-router";

import { errorMessage } from "@/api/http";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    await auth.login(email.value, password.value);
    router.push({ name: "dashboard" });
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="auth-page">
    <!-- Background grid decoration -->
    <div class="bg-grid" aria-hidden="true"></div>
    <div class="bg-glow" aria-hidden="true"></div>

    <div class="auth-card animate-fade-up">
      <!-- Logo -->
      <div class="auth-logo">
        <div class="brand-mark logo-icon">B</div>
        <div class="logo-text">
          <span class="logo-name">BIP</span>
          <span class="logo-sub">Bourse d'Investissement Participatif</span>
        </div>
      </div>

      <div class="auth-divider"></div>

      <div class="auth-header">
        <h1>Welcome back</h1>
        <p>Sign in to your simulated trading account</p>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <div class="field">
          <label for="email">Email address</label>
          <InputText
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            autofocus
            fluid
          />
        </div>

        <div class="field">
          <label for="password">Password</label>
          <Password
            id="password"
            v-model="password"
            :feedback="false"
            toggle-mask
            required
            fluid
            placeholder="••••••••"
          />
        </div>

        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

        <Button
          type="submit"
          label="Sign in"
          :loading="loading"
          fluid
          class="submit-btn"
        >
          <template #icon>
            <i class="pi pi-arrow-right" style="margin-left: 0.5rem;"></i>
          </template>
        </Button>
      </form>

      <p class="auth-switch">
        No account yet?
        <router-link to="/register">Create one</router-link>
      </p>

      <div class="demo-box">
        <div class="demo-title">
          <i class="pi pi-info-circle"></i>
          Demo credentials
        </div>
        <div class="demo-creds">
          <div class="cred-row">
            <span class="cred-role">Investor</span>
            <code>investor@bip.demo</code>
          </div>
          <div class="cred-row">
            <span class="cred-role">Admin</span>
            <code>admin@bip.demo</code>
          </div>
          <div class="cred-row">
            <span class="cred-role">Back-office</span>
            <code>backoffice@bip.demo</code>
          </div>
          <div class="cred-hint">Password: <code>DemoPass123!</code></div>
        </div>
      </div>
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

/* Decorative background */
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

/* Auth card */
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

/* Logo */
.auth-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0;
}
.logo-icon {
  width: 44px;
  height: 44px;
  font-size: 1.35rem;
}
.logo-text { display: flex; flex-direction: column; }
.logo-name {
  font-size: var(--text-lg);
  font-weight: 800;
  letter-spacing: var(--tracking-tight);
  color: var(--text-primary);
  line-height: 1.1;
}
.logo-sub {
  font-size: var(--text-2xs);
  color: var(--text-muted);
  margin-top: 3px;
  letter-spacing: var(--tracking-normal);
}

.auth-divider {
  height: 1px;
  background: var(--surface-border);
  margin: 1.5rem 0;
}

/* Header */
.auth-header { margin-bottom: 1.5rem; }
.auth-header h1 {
  font-size: var(--text-xl);
  font-weight: 800;
  letter-spacing: var(--tracking-tight);
  color: var(--text-primary);
  margin-bottom: 0.3rem;
}
.auth-header p {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

/* Form */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.field label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
}
.submit-btn {
  margin-top: 0.25rem;
}

/* Switch link */
.auth-switch {
  margin-top: 1.25rem;
  text-align: center;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

/* Demo box */
.demo-box {
  margin-top: 1.5rem;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  padding: 0.875rem 1rem;
}
.demo-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: var(--text-2xs);
  font-weight: 700;
  letter-spacing: var(--tracking-label);
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}
.demo-creds {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.cred-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: var(--text-xs);
}
.cred-role {
  width: 84px;
  color: var(--text-muted);
  font-weight: 600;
  flex-shrink: 0;
}
code {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--text-xs);
  color: var(--bip-gold);
  background: rgba(240,180,41,0.07);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}
.cred-hint {
  margin-top: 0.35rem;
  font-size: var(--text-xs);
  color: var(--text-muted);
}
</style>
