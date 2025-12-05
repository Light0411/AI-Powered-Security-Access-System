<template>
  <div class="space-y-6">
    <section class="card">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Passes</p>
          <h2 class="text-xl font-semibold">Issued passes</h2>
        </div>
        <button class="rounded-xl border border-white/10 px-3 py-1 text-xs" @click="admin.reloadPasses">
          Refresh
        </button>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="pb-2 font-normal">Holder</th>
              <th class="pb-2 font-normal">Role</th>
              <th class="pb-2 font-normal">Plan</th>
              <th class="pb-2 font-normal">Validity</th>
              <th class="pb-2 font-normal">Payment</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="pass in sortedPasses"
              :key="pass.id"
              class="border-t border-white/5"
              :class="isExpired(pass) ? 'bg-rose-950/30' : ''"
            >
              <td class="py-2">{{ admin.getUserById(pass.user_id)?.name ?? pass.user_id }}</td>
              <td class="py-2 capitalize">{{ pass.role }}</td>
              <td class="py-2">
                <div class="font-semibold">{{ planLabel(pass.plan_type) }}</div>
                <div class="text-xs text-slate-400">{{ formatRm(pass.price_rm) }}</div>
              </td>
              <td class="py-2 text-slate-400">
                {{ formatDate(pass.valid_from) }} → {{ formatDate(pass.valid_to) }}
              </td>
              <td class="py-2">
                <span :class="pass.is_paid ? 'text-emerald-300' : 'text-amber-300'">
                  {{ pass.is_paid ? 'Paid' : 'Awaiting payment' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="card">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Applications</p>
          <h2 class="text-xl font-semibold">Pending approvals</h2>
        </div>
        <div class="flex items-center gap-3">
          <select v-model="statusFilter" class="rounded-xl border border-white/10 bg-white/5 px-3 py-1 text-sm">
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button class="rounded-xl border border-white/10 px-3 py-1 text-xs" @click="refreshApplications">
            Refresh
          </button>
        </div>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="pb-2 font-normal">Applicant</th>
              <th class="pb-2 font-normal">Plan</th>
              <th class="pb-2 font-normal">Vehicles</th>
              <th class="pb-2 font-normal">Status</th>
              <th class="pb-2 font-normal"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredApplications.length">
              <td colspan="5" class="py-4 text-center text-slate-500">No applications found</td>
            </tr>
            <tr v-for="application in filteredApplications" :key="application.id" class="border-t border-white/5">
              <td class="py-2">
                <div class="font-semibold">{{ admin.getUserById(application.user_id)?.name ?? application.user_id }}</div>
                <div class="text-xs text-slate-400">{{ formatDate(application.submitted_at) }}</div>
              </td>
              <td class="py-2">
                {{ planLabel(application.plan_type) }}
                <div class="text-xs text-slate-400">{{ formatRm(planPrice(application.plan_type)) }}</div>
              </td>
              <td class="py-2">
                <div v-if="application.vehicles.length" class="flex flex-wrap gap-2">
                  <span
                    v-for="plate in application.vehicles"
                    :key="plate"
                    class="rounded-xl border border-white/10 px-3 py-1 font-mono text-xs"
                    >{{ plate }}</span
                  >
                </div>
                <span v-else class="text-xs text-slate-500">None</span>
              </td>
              <td class="py-2">
                <span
                  :class="{
                    'text-amber-300': application.status === 'pending',
                    'text-emerald-300': application.status === 'approved',
                    'text-rose-300': application.status === 'rejected',
                  }"
                >
                  {{ application.status }}
                </span>
                <p v-if="application.review_note" class="text-xs text-slate-400">{{ application.review_note }}</p>
              </td>
              <td class="py-2 text-right">
                <div v-if="application.status === 'pending'" class="flex gap-2 text-xs">
                  <button class="rounded-xl border border-emerald-400/40 px-3 py-1 text-emerald-200" @click="confirmDecision(application, 'approved')">
                    Approve
                  </button>
                  <button class="rounded-xl border border-rose-400/40 px-3 py-1 text-rose-200" @click="confirmDecision(application, 'rejected')">
                    Reject
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { format } from 'date-fns'

import { useAdminStore } from '@/stores/admin'
import type { Pass, PassApplication } from '@/services/api'

const admin = useAdminStore()
const statusFilter = ref<'all' | 'pending' | 'approved' | 'rejected'>('pending')

const planMap = computed(() => Object.fromEntries(admin.passPlans.map((plan) => [plan.plan_type, plan])))

const sortedPasses = computed(() => {
  return [...admin.passes].sort((a, b) => new Date(b.valid_to).getTime() - new Date(a.valid_to).getTime())
})

const filteredApplications = computed(() => {
  if (statusFilter.value === 'all') {
    return admin.passApplications
  }
  return admin.passApplications.filter((app) => app.status === statusFilter.value)
})

const formatDate = (iso: string) => format(new Date(iso), 'dd MMM yyyy')
const formatRm = (value: number) => `RM ${value.toFixed(2)}`
const planLabel = (planType: string) => planMap.value[planType]?.label ?? planType
const planPrice = (planType: string) => planMap.value[planType]?.price_rm ?? 0

const isExpired = (pass: Pass) => new Date(pass.valid_to).getTime() < Date.now()

const refreshApplications = async () => {
  await admin.reloadPassApplications(statusFilter.value === 'all' ? undefined : statusFilter.value)
}

const confirmDecision = async (application: PassApplication, status: 'approved' | 'rejected') => {
  const note = window.prompt('Optional note for the applicant?') ?? undefined
  await admin.reviewApplication(application.id, {
    status,
    reviewer_id: 'ADMIN-PORTAL',
    note: note || undefined,
  })
}

onMounted(async () => {
  if (!admin.passes.length) {
    await admin.bootstrap()
  } else if (!admin.passPlans.length) {
    await admin.loadPassPlans()
  } else {
    await Promise.all([admin.reloadPasses(), admin.reloadPassApplications()])
  }
})

watch(statusFilter, async () => {
  await refreshApplications()
})
</script>
