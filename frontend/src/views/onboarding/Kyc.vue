<script setup lang="ts">
import Button from "primevue/button";
import DatePicker from "primevue/datepicker";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import ProgressSpinner from "primevue/progressspinner";
import Select from "primevue/select";
import { useToast } from "primevue/usetoast";
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { errorMessage } from "@/api/http";
import { useKycStore } from "@/stores/kyc";

const kyc = useKycStore();
const toast = useToast();
const router = useRouter();

const fullLegalName = ref("");
const birthDate = ref<Date | null>(null);
const country = ref<string | null>(null);
const idDocumentType = ref<string | null>(null);
const idDocumentNumber = ref("");

const saving = ref(false);
const submitting = ref(false);
const error = ref("");

const countries = [
  { label: "Côte d'Ivoire", value: "CI" },
  { label: "Sénégal", value: "SN" },
  { label: "Burkina Faso", value: "BF" },
  { label: "Mali", value: "ML" },
  { label: "Togo", value: "TG" },
  { label: "Bénin", value: "BJ" },
  { label: "Niger", value: "NE" },
  { label: "Guinée-Bissau", value: "GW" },
  { label: "France", value: "FR" },
  { label: "United States", value: "US" },
  { label: "Other", value: "XX" },
];
const documentTypes = [
  { label: "Passport", value: "passport" },
  { label: "National ID", value: "national_id" },
  { label: "Driver's License", value: "drivers_license" },
];

function toIso(d: Date | null) {
  if (!d) return undefined;
  return d.toISOString().slice(0, 10);
}

onMounted(async () => {
  await kyc.fetchMine();
  syncFields();
});

watch(() => kyc.current, syncFields);

function syncFields() {
  const k = kyc.current;
  if (!k) return;
  fullLegalName.value = k.full_legal_name ?? "";
  birthDate.value = k.birth_date ? new Date(k.birth_date) : null;
  country.value = k.country;
  idDocumentType.value = k.id_document_type;
  idDocumentNumber.value = k.id_document_number ?? "";
}

const canEdit = computed(() => kyc.current?.status === "draft" || kyc.current?.status === "rejected");

const stepStatus = computed(() => {
  const s = kyc.current?.status;
  if (s === "validated") return "validated";
  if (s === "submitted") return "submitted";
  if (s === "rejected")  return "rejected";
  return "draft";
});

async function saveDraft() {
  saving.value = true;
  error.value = "";
  try {
    await kyc.saveDraft({
      full_legal_name: fullLegalName.value,
      birth_date: toIso(birthDate.value) as any,
      country: country.value,
      id_document_type: idDocumentType.value,
      id_document_number: idDocumentNumber.value,
    });
    toast.add({ severity: "success", summary: "Draft saved", life: 2500 });
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    saving.value = false;
  }
}

async function submit() {
  submitting.value = true;
  error.value = "";
  try {
    await saveDraft();
    await kyc.submit();
    toast.add({ severity: "success", summary: "KYC submitted", detail: "Your file is now under review.", life: 3500 });
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <div class="kyc-page">
    <div class="bg-grid" aria-hidden="true"></div>
    <div class="bg-glow" aria-hidden="true"></div>

    <div class="kyc-card animate-fade-up">
      <!-- Header -->
      <div class="kyc-logo">
        <div class="brand-mark logo-icon">B</div>
        <div>
          <div class="logo-name">BIP</div>
          <div class="logo-sub">Identity Verification</div>
        </div>
      </div>

      <div class="kyc-divider"></div>

      <!-- Progress steps -->
      <div class="steps">
        <div class="step" :class="{ active: true, done: ['submitted','validated'].includes(stepStatus) }">
          <div class="step-circle">
            <i v-if="['submitted','validated'].includes(stepStatus)" class="pi pi-check"></i>
            <span v-else>1</span>
          </div>
          <span class="step-label">Personal info</span>
        </div>
        <div class="step-line"></div>
        <div class="step" :class="{ active: stepStatus === 'submitted' || stepStatus === 'validated', done: stepStatus === 'validated' }">
          <div class="step-circle">
            <i v-if="stepStatus === 'validated'" class="pi pi-check"></i>
            <span v-else>2</span>
          </div>
          <span class="step-label">Under review</span>
        </div>
        <div class="step-line"></div>
        <div class="step" :class="{ active: stepStatus === 'validated', done: stepStatus === 'validated' }">
          <div class="step-circle">
            <i v-if="stepStatus === 'validated'" class="pi pi-check"></i>
            <span v-else>3</span>
          </div>
          <span class="step-label">Activated</span>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="kyc.loading && !kyc.current" class="loading-state">
        <ProgressSpinner style="width:2rem;height:2rem" />
        <span>Loading your KYC status…</span>
      </div>

      <template v-else-if="kyc.current">
        <!-- Status messages -->
        <Message v-if="stepStatus === 'validated'" severity="success" :closable="false">
          <div class="msg-content">
            <i class="pi pi-shield-check"></i>
            <div>
              <strong>Account verified and active.</strong>
              You're ready to trade on the simulated market.
            </div>
          </div>
        </Message>

        <Message v-else-if="stepStatus === 'submitted'" severity="info" :closable="false">
          <div class="msg-content">
            <i class="pi pi-clock"></i>
            <div>
              <strong>Awaiting review.</strong>
              Your KYC file has been submitted to the back-office.
            </div>
          </div>
        </Message>

        <Message v-else-if="stepStatus === 'rejected'" severity="warn" :closable="false">
          <div class="msg-content">
            <i class="pi pi-exclamation-triangle"></i>
            <div>
              <strong>Submission rejected.</strong>
              Reason: {{ kyc.current.rejection_reason }}. Please update and resubmit.
            </div>
          </div>
        </Message>

        <!-- Form -->
        <form v-if="canEdit" class="kyc-form" @submit.prevent="submit">
          <div class="form-section">
            <div class="section-title">Personal Information</div>
            <div class="form-grid">
              <div class="field">
                <label>Full legal name</label>
                <InputText v-model="fullLegalName" required fluid placeholder="As on your ID document" />
              </div>
              <div class="field">
                <label>Date of birth</label>
                <DatePicker v-model="birthDate" date-format="yy-mm-dd" show-icon fluid />
              </div>
              <div class="field">
                <label>Country of residence</label>
                <Select v-model="country" :options="countries" option-label="label" option-value="value" fluid />
              </div>
            </div>
          </div>

          <div class="form-section">
            <div class="section-title">Identity Document</div>
            <div class="form-grid">
              <div class="field">
                <label>Document type</label>
                <Select v-model="idDocumentType" :options="documentTypes" option-label="label" option-value="value" fluid />
              </div>
              <div class="field">
                <label>Document number</label>
                <InputText v-model="idDocumentNumber" required fluid placeholder="e.g. A1234567" />
              </div>
            </div>
          </div>

          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>

          <div class="form-disclaimer">
            <i class="pi pi-info-circle"></i>
            This is a simulated KYC for demo purposes only. No real identity verification is performed.
          </div>

          <div class="form-actions">
            <Button label="Save draft" severity="secondary" :loading="saving" @click.prevent="saveDraft" />
            <Button type="submit" label="Submit for review" :loading="submitting" />
          </div>
        </form>

        <!-- Validated CTA -->
        <Button
          v-if="stepStatus === 'validated'"
          label="Go to dashboard"
          fluid
          style="margin-top:1.5rem"
          @click="router.push({ name: 'dashboard' })"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.kyc-page {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface-0);
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}
.bg-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
}
.bg-glow {
  position: absolute; top: -20%; left: 50%; transform: translateX(-50%);
  width: 700px; height: 400px;
  background: radial-gradient(ellipse at center, rgba(99,102,241,0.06) 0%, transparent 70%);
  pointer-events: none;
}
.kyc-card {
  width: 100%; max-width: 580px;
  background: linear-gradient(145deg, var(--surface-1) 0%, var(--surface-2) 100%);
  border: 1px solid var(--surface-border-strong);
  border-radius: var(--radius-xl);
  padding: 2.25rem;
  box-shadow: 0 25px 60px rgba(0,0,0,0.5);
  position: relative; z-index: 1;
}
.kyc-logo { display: flex; align-items: center; gap: 0.75rem; }
.logo-icon {
  width: 40px; height: 40px;
  font-size: 1.2rem;
}
.logo-name { font-size: var(--text-md); font-weight: 800; letter-spacing: var(--tracking-tight); color: var(--text-primary); line-height: 1.1; }
.logo-sub  { font-size: var(--text-xs); color: var(--text-muted); margin-top: 3px; }
.kyc-divider { height: 1px; background: var(--surface-border); margin: 1.5rem 0; }

/* Steps */
.steps {
  display: flex; align-items: center; margin-bottom: 1.75rem;
}
.step { display: flex; align-items: center; flex-direction: column; gap: 0.4rem; }
.step-circle {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: var(--text-sm); font-weight: 800;
  background: var(--surface-3);
  border: 2px solid var(--surface-border-strong);
  color: var(--text-muted);
  transition: all 0.3s ease;
}
.step.active .step-circle {
  background: rgba(240,180,41,0.15);
  border-color: var(--bip-gold);
  color: var(--bip-gold);
}
.step.done .step-circle {
  background: rgba(16,185,129,0.15);
  border-color: var(--bip-green);
  color: var(--bip-green);
}
.step-label { font-size: var(--text-2xs); font-weight: 600; color: var(--text-muted); white-space: nowrap; }
.step.active .step-label { color: var(--bip-gold); }
.step.done  .step-label  { color: var(--bip-green); }
.step-line { flex: 1; height: 2px; background: var(--surface-border); margin: 0 0.5rem; margin-bottom: 1rem; }

/* Loading */
.loading-state {
  display: flex; align-items: center; justify-content: center;
  gap: 0.75rem; padding: 2rem;
  color: var(--text-secondary); font-size: 0.875rem;
}

/* Form */
.kyc-form { display: flex; flex-direction: column; gap: 1.5rem; margin-top: 1.25rem; }
.form-section { display: flex; flex-direction: column; gap: 1rem; }
.section-title {
  font-size: var(--text-xs); font-weight: 700;
  letter-spacing: var(--tracking-label); text-transform: uppercase;
  color: var(--text-secondary); border-bottom: 1px solid var(--surface-border);
  padding-bottom: 0.5rem;
}
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.875rem; }
@media (max-width: 520px) { .form-grid { grid-template-columns: 1fr; } }
.field { display: flex; flex-direction: column; gap: 0.4rem; }
.field label { font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); }
.form-disclaimer {
  display: flex; align-items: flex-start; gap: 0.5rem;
  font-size: var(--text-xs); color: var(--text-muted);
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--surface-border);
  border-radius: var(--radius-md);
  padding: 0.75rem 0.875rem;
  line-height: 1.55;
}
.form-disclaimer .pi { color: var(--bip-blue); flex-shrink: 0; margin-top: 1px; }
.form-actions { display: flex; gap: 0.75rem; justify-content: flex-end; }

/* Message content */
.msg-content { display: flex; align-items: flex-start; gap: 0.75rem; }
.msg-content .pi { font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }
</style>
