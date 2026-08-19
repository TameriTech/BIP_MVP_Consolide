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

const fullName = ref("");
const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    await auth.register({ email: email.value, password: password.value, full_name: fullName.value });
    router.push({ name: "onboarding-kyc" });
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
      <!-- Logo -->
      <div class="auth-logo">
        <div class="logo-icon">₿</div>
        <div class="logo-text">
          <span class="logo-name">BIP</span>
          <span class="logo-sub">Bourse d'Investissement Participatif</span>
        </div>
      </div>

      <div class="auth-divider"></div>

      <div class="auth-header">
        <h1>Create your account</h1>
        <p>Start your simulated investment journey — no real money, ever.</p>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <div class="field">
          <label for="fullname">Full name</label>
          <InputText
            id="fullname"
            v-model="fullName"
            placeholder="Jean-Paul Dupont"
            required
            autofocus
            fluid
          />
        </div>

        <div class="field">
          <label for="email">Email address</label>
          <InputText
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            fluid
          />
        </div>

        <div class="field">
          <label for="password">Password</label>
          <Password
            id="password"
            v-model="password"
            toggle-mask
            required
            fluid
            placeholder="Min. 8 characters"
          />
        </div>

        <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

        <Button type="submit" label="Create account" :loading="loading" fluid class="submit-btn" />
      </form>

      <p class="auth-switch">
        Already have an account?
        <router-link to="/login">Sign in</router-link>
      </p>

      <div class="info-box">
        <i class="pi pi-shield"></i>
        This is a simulation platform. No real funds are collected or traded.
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
  background: radial-gradient(ellipse at center, rgba(59,130,246,0.08) 0%, transparent 70%);
  pointer-events: none;
}
.auth-card {
  width: 100%;
  max-width: 440px;
  background: linear-gradient(145deg, var(--surface-1) 0%, var(--surface-2) 100%);
  border: 1px solid var(--surface-border-strong);
  border-radius: var(--radius-xl);
  padding: 2.25rem;
  box-shadow: 0 25px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04);
  position: relative;
  z-index: 1;
}
.auth-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.logo-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #f0b429, #d97706);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #1a1000;
  font-weight: 900;
  box-shadow: 0 4px 16px rgba(240,180,41,0.35);
  flex-shrink: 0;
}
.logo-text { display: flex; flex-direction: column; }
.logo-name {
  font-size: 1.3rem;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  line-height: 1;
}
.logo-sub {
  font-size: 0.62rem;
  color: var(--text-muted);
  margin-top: 2px;
}
.auth-divider {
  height: 1px;
  background: var(--surface-border);
  margin: 1.5rem 0;
}
.auth-header { margin-bottom: 1.5rem; }
.auth-header h1 {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 0.3rem;
}
.auth-header p {
  font-size: 0.85rem;
  color: var(--text-secondary);
}
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
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}
.submit-btn { margin-top: 0.25rem; }
.auth-switch {
  margin-top: 1.25rem;
  text-align: center;
  font-size: 0.85rem;
  color: var(--text-secondary);
}
.info-box {
  margin-top: 1.25rem;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.78rem;
  color: var(--text-muted);
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  padding: 0.75rem;
  line-height: 1.5;
}
.info-box .pi { color: var(--bip-blue); margin-top: 1px; flex-shrink: 0; }
</style>
