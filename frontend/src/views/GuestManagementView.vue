<template>
  <div class="space-y-6">
    <section class="grid gap-6 lg:grid-cols-3">
      <div class="card space-y-4 lg:col-span-2">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-widest text-slate-400">Guest sessions</p>
            <h2 class="text-xl font-semibold">Live timers</h2>
          </div>
          <button class="rounded-xl border border-white/10 px-3 py-1 text-xs" @click="guest.refreshSessions">
            Refresh
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead class="text-left text-slate-400">
              <tr>
                <th class="pb-2 font-normal">Plate</th>
                <th class="pb-2 font-normal">Status</th>
                <th class="pb-2 font-normal">Minutes</th>
                <th class="pb-2 font-normal">Fee</th>
                <th class="pb-2 font-normal"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="session in guest.sessions" :key="session.id" class="border-t border-white/5">
                <td class="py-2 font-mono tracking-widest">{{ session.plate_text }}</td>
                <td class="py-2 capitalize">{{ session.status }}</td>
                <td class="py-2 text-slate-400">{{ displayMinutes(session) }}</td>
                <td class="py-2 text-slate-400">RM {{ displayFee(session) }}</td>
                <td class="py-2 flex gap-2 text-xs">
                  <button
                    v-if="session.status === 'open'"
                    class="rounded-xl border border-white/10 px-3 py-1"
                    @click="guest.stopSession(session.id)"
                  >
                    Close
                  </button>
                  <button
                    v-if="session.status !== 'paid'"
                    class="rounded-xl border border-brand-500/40 px-3 py-1 text-brand-200"
                    @click="guest.paySession(session.id)"
                  >
                    Charge Touch 'n Go
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="card space-y-4">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Start session</p>
          <h2 class="text-xl font-semibold">Walk-in guest</h2>
        </div>
        <div class="rounded-2xl border border-white/5 bg-slate-900/40 p-4 text-sm">
          <p class="text-xs uppercase tracking-widest text-slate-500">Live metrics</p>
          <div class="mt-2 flex items-center justify-between">
            <div>
              <p class="text-xs text-slate-400">Open sessions</p>
              <p class="text-xl font-semibold text-white">{{ liveTotals.open }}</p>
            </div>
            <div class="text-right">
              <p class="text-xs text-slate-400">Fees billed</p>
              <p class="text-xl font-semibold text-emerald-300">RM {{ liveTotals.due.toFixed(2) }}</p>
            </div>
          </div>
        </div>
        <form class="space-y-3" @submit.prevent="createSession">
          <input v-model="plate" placeholder="Plate" class="form-input uppercase tracking-widest" required />
          <button class="btn-primary w-full" type="submit">Start</button>
        </form>
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Rate card</p>
          <div class="mt-3 space-y-3">
            <div>
              <p class="text-xs text-slate-400">Base rate</p>
              <input v-model.number="baseRate" type="number" step="0.1" class="form-input" />
            </div>
            <div>
              <p class="text-xs text-slate-400">Per-minute</p>
              <input v-model.number="perMinute" type="number" step="0.1" class="form-input" />
            </div>
            <button class="rounded-xl border border-white/10 px-4 py-2 text-sm" @click="saveRate">
              Save rate
            </button>
          </div>
        </div>
        <p v-if="guest.lastPayment" class="text-xs text-emerald-300">
          Payment {{ guest.lastPayment.id }} confirmed for {{ formatRm(guest.lastPayment.amount) }}
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { useGuestStore } from '@/stores/guest'
import type { GuestSession } from '@/services/api'

const guest = useGuestStore()
const plate = ref('')
const baseRate = ref(0)
const perMinute = ref(0)

const hydrateRates = () => {
  if (guest.rate) {
    baseRate.value = guest.rate.base_rate
    perMinute.value = guest.rate.per_minute_rate
  }
}

const createSession = async () => {
  await guest.startSession(plate.value.toUpperCase())
  plate.value = ''
}

const saveRate = async () => {
  await guest.updateRate({ base_rate: baseRate.value, per_minute_rate: perMinute.value })
}

const liveTotals = computed(() => {
  const open = guest.sessions.filter((session) => session.status === 'open').length
  const due = guest.sessions.reduce((sum, session) => sum + computeFeeValue(session), 0)
  return {
    open,
    due,
  }
})

const displayMinutes = (session: GuestSession) => {
  if (session.minutes) {
    return session.minutes
  }
  const start = new Date(session.start_time)
  const diffMs = Date.now() - start.getTime()
  return Math.max(1, Math.floor(diffMs / 60000))
}

const computeFeeValue = (session: GuestSession) => {
  if (session.status !== 'open' && session.fee != null) {
    return session.fee
  }
  if (!guest.rate) {
    return 0
  }
  const minutes = displayMinutes(session)
  return guest.rate.base_rate + guest.rate.per_minute_rate * Math.max(0, minutes)
}

const displayFee = (session: GuestSession) => {
  if (!guest.rate && session.fee == null) {
    return 'N/A'
  }
  return computeFeeValue(session).toFixed(2)
}

const formatRm = (amount: number) => `RM ${amount.toFixed(2)}`

watch(() => guest.rate, hydrateRates, { immediate: true })

onMounted(() => {
  if (!guest.sessions.length) {
    guest.bootstrap()
  }
})
</script>

<style scoped>
.form-input {
  @apply w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm;
}
</style>
