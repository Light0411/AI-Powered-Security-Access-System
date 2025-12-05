<template>
  <div class="grid gap-6 lg:grid-cols-3">
    <section class="card lg:col-span-2 space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Digital pass</p>
          <h2 class="text-xl font-semibold">{{ activeUser?.name ?? 'Select user' }}</h2>
        </div>
        <select v-model="selectedUserId" class="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm">
          <option value="" disabled>Select user</option>
          <option v-for="user in admin.users" :key="user.id" :value="user.id">
            {{ user.name }} · {{ user.role }}
          </option>
        </select>
      </div>
      <div v-if="activePass" class="rounded-2xl border border-emerald-400/30 bg-green-950/30 p-6 space-y-3">
        <p class="text-sm uppercase tracking-[0.3em] text-emerald-200">Access level</p>
        <p class="mt-3 text-4xl font-bold text-white">{{ activePass.role }}</p>
        <p class="text-sm text-emerald-200">
          {{ activePlanDetails?.label ?? activePass.plan_type }} · {{ formatRm(activePass.price_rm) }}
        </p>
        <p class="text-xs text-emerald-100">
          Valid {{ formatDate(activePass.valid_from) }} → {{ formatDate(activePass.valid_to) }}
        </p>
        <p class="text-sm" :class="activePass.is_paid ? 'text-emerald-300' : 'text-amber-300'">
          {{ activePass.is_paid ? 'Paid' : 'Awaiting payment' }}
        </p>
        <div v-if="!activePass.is_paid" class="space-y-2 rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200">
          <p>Outstanding: {{ formatRm(activePass.price_rm) }}</p>
          <button class="btn-primary w-full text-sm" type="button" :disabled="paying" @click="payInvoice">
            {{ paying ? 'Processing…' : 'Pay from Wallet' }}
          </button>
          <p v-if="payError" class="text-xs text-rose-300">{{ payError }}</p>
        </div>
      </div>
      <div v-else class="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-slate-200">
        No active pass yet. Submit an application and wait for approval to receive an invoice.
      </div>
      <div class="rounded-2xl border border-white/10 bg-white/5 p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-widest text-slate-400">Latest application</p>
            <h3 class="text-xl font-semibold text-white">
              {{ latestApplication ? activeUser?.name ?? 'Applicant' : 'No application yet' }}
            </h3>
          </div>
          <button class="text-xs text-brand-300 hover:text-brand-200" type="button" @click="refreshApplicantData">
            Refresh
          </button>
        </div>
        <div v-if="latestApplication" class="mt-4 space-y-3">
          <div class="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Status</p>
              <p class="text-2xl font-semibold capitalize" :class="statusClass(latestApplication.status)">
                {{ latestApplication.status }}
              </p>
              <p class="text-xs text-slate-400">
                Submitted {{ formatDate(latestApplication.submitted_at) }}
                <span v-if="latestApplication.reviewed_at">
                  �� Reviewed {{ formatDate(latestApplication.reviewed_at) }}
                </span>
              </p>
            </div>
            <div class="text-right">
              <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Plan</p>
              <p class="text-lg font-semibold text-white">{{ planLabel(latestApplication.plan_type) }}</p>
              <p class="text-xs text-slate-400 capitalize">Role: {{ latestApplication.role }}</p>
            </div>
          </div>
          <div>
            <p class="text-xs uppercase tracking-[0.3em] text-slate-500">Vehicles</p>
            <div v-if="latestApplication.vehicles.length" class="mt-2 flex flex-wrap gap-2">
              <span
                v-for="plate in latestApplication.vehicles"
                :key="plate"
                class="rounded-xl border border-white/10 px-3 py-1 font-mono text-xs"
                >{{ plate }}</span
              >
            </div>
            <p v-else class="text-xs text-slate-500">No vehicles submitted</p>
          </div>
          <p class="text-sm" :class="statusClass(latestApplication.status)">
            {{ latestApplicationMessage }}
          </p>
          <p v-if="latestApplication.review_note" class="text-xs text-slate-300">
            Reviewer note: {{ latestApplication.review_note }}
          </p>
        </div>
        <div v-else class="mt-4 text-sm text-slate-400">
          Submit a pass application from the mobile app or client portal to start the review workflow.
        </div>
      </div>
      <div>
        <p class="text-sm uppercase tracking-widest text-slate-400">Linked vehicles</p>
        <div class="mt-2 flex flex-wrap gap-3 text-lg font-mono">
          <span v-for="vehicle in activeVehicles" :key="vehicle.id" class="rounded-xl border border-white/10 px-4 py-2">
            {{ vehicle.plate_text }}
          </span>
          <span v-if="!activeVehicles.length" class="text-sm text-slate-500">No vehicles linked</span>
        </div>
      </div>
      <div>
        <div class="flex items-center justify-between">
          <p class="text-sm uppercase tracking-widest text-slate-400">Parking availability</p>
          <button class="text-xs text-brand-300 hover:text-brand-200" type="button" @click="loadOccupancy">Refresh</button>
        </div>
        <div class="mt-4 space-y-3">
          <div v-for="lot in occupancy" :key="lot.id">
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span>{{ lot.name }}</span>
              <span>{{ lot.occupied }} / {{ lot.capacity }}</span>
            </div>
            <div class="mt-1 h-2 rounded-full bg-white/5">
              <div class="h-2 rounded-full bg-brand-500" :style="{ width: Math.min(100, lot.percent) + '%' }"></div>
            </div>
          </div>
          <p v-if="!occupancy.length" class="text-xs text-slate-500">Fetching live occupancy...</p>
        </div>
      </div>
    </section>
    <section class="card space-y-4">
      <div>
        <p class="text-sm uppercase tracking-widest text-slate-400">Upgrade request</p>
        <h2 class="text-xl font-semibold">Role change</h2>
      </div>
      <form class="space-y-3" @submit.prevent="submit">
        <textarea v-model="reason" rows="4" placeholder="Intent (mock submission)" class="form-input"></textarea>
        <input type="file" @change="handleFile" class="text-sm" />
        <button class="btn-primary w-full" type="submit">Send request</button>
      </form>
      <p v-if="submitted" class="text-xs text-emerald-300">Submitted for review</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { format } from 'date-fns'

import type { ParkingVenueStatus, PassApplication } from '@/services/api'
import { fetchParkingOverview, payPassInvoice } from '@/services/api'
import { useAdminStore } from '@/stores/admin'

const admin = useAdminStore()
const selectedUserId = ref('')
const reason = ref('')
const submitted = ref(false)
const occupancy = ref<ParkingVenueStatus[]>([])
const paying = ref(false)
const payError = ref<string | null>(null)

const activeUser = computed(() => admin.users.find((user) => user.id === selectedUserId.value))
const activePass = computed(() => admin.passes.find((pass) => pass.user_id === selectedUserId.value) ?? null)
const activeVehicles = computed(() => admin.vehicles.filter((vehicle) => vehicle.user_id === selectedUserId.value))
const planLookup = computed(() => Object.fromEntries(admin.passPlans.map((plan) => [plan.plan_type, plan])))
const activePlanDetails = computed(() => (activePass.value ? planLookup.value[activePass.value.plan_type] : null))
const userApplications = computed(() => admin.passApplications.filter((app) => app.user_id === selectedUserId.value))
const latestApplication = computed(() => userApplications.value[0] ?? null)
const latestApplicationMessage = computed(() => {
  const application = latestApplication.value
  if (!application) {
    return 'Submit a pass application to start the approval workflow.'
  }
  if (application.status === 'pending') {
    return 'Pending admin approval.'
  }
  if (application.status === 'approved') {
    if (activePass.value?.is_paid) {
      return 'Approved and paid. LPR will honor this pass.'
    }
    return 'Approved. Pay the wallet invoice below to activate access.'
  }
  return application.review_note || 'Rejected. Update your details and resubmit.'
})

const formatDate = (iso?: string | null) => (iso ? format(new Date(iso), 'dd MMM yyyy') : '—')
const formatRm = (value: number) => `RM ${value.toFixed(2)}`
const planLabel = (planType: string) => planLookup.value[planType]?.label ?? planType
const statusClass = (status: PassApplication['status']) => {
  if (status === 'approved') return 'text-emerald-300'
  if (status === 'rejected') return 'text-rose-300'
  return 'text-amber-300'
}

const handleFile = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files?.length) {
    submitted.value = false
  }
}

const submit = () => {
  submitted.value = true
  reason.value = ''
}

const setDefaultUser = () => {
  if (!selectedUserId.value) {
    const first = admin.users[0]
    if (first) {
      selectedUserId.value = first.id
    }
  }
}

const loadOccupancy = async () => {
  const data = await fetchParkingOverview()
  occupancy.value = data.venues
}

const refreshApplicantData = async () => {
  await Promise.all([admin.reloadPasses(), admin.reloadPassApplications()])
}

const payInvoice = async () => {
  if (!activePass.value || !selectedUserId.value) return
  paying.value = true
  payError.value = null
  try {
    await payPassInvoice(activePass.value.id, selectedUserId.value)
    await admin.reloadPasses()
  } catch (err) {
    payError.value = err instanceof Error ? err.message : 'Payment failed'
  } finally {
    paying.value = false
  }
}

onMounted(async () => {
  if (!admin.users.length) {
    await admin.bootstrap()
  } else {
    const pending: Promise<unknown>[] = [admin.reloadPassApplications()]
    if (!admin.passes.length) pending.push(admin.reloadPasses())
    if (!admin.passPlans.length) pending.push(admin.loadPassPlans())
    await Promise.all(pending)
  }
  setDefaultUser()
  await loadOccupancy()
})
</script>

<style scoped>
.form-input {
  @apply w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm;
}
</style>
