<template>
  <div class="space-y-6">
    <section class="grid gap-4 md:grid-cols-4">
      <div v-for="tile in kpis" :key="tile.label" class="card">
        <p class="text-xs uppercase tracking-widest text-slate-400">{{ tile.label }}</p>
        <p class="mt-3 text-3xl font-semibold">{{ tile.value }}</p>
        <p class="text-sm text-slate-400">{{ tile.hint }}</p>
      </div>
    </section>

    <section class="grid gap-6 lg:grid-cols-2">
      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.3em] text-slate-400">Traffic</p>
            <h2 class="text-xl font-semibold">Gate frequency</h2>
          </div>
          <button class="rounded-xl border border-white/10 px-3 py-1 text-xs" @click="bootstrap">
            Refresh
          </button>
        </div>
        <div class="mt-4">
          <Line v-if="lineData" :data="lineData" :options="chartOptions" height="220" />
        </div>
      </div>
      <div class="card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-[0.3em] text-slate-400">Distribution</p>
            <h2 class="text-xl font-semibold">Roles vs vehicles</h2>
          </div>
        </div>
        <div class="mt-4">
          <Bar v-if="barData" :data="barData" :options="chartOptions" height="220" />
        </div>
      </div>
    </section>

    <section class="card">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Guest revenue</p>
          <h2 class="text-xl font-semibold">Fee trend</h2>
        </div>
      </div>
      <div class="mt-4">
        <Line v-if="guestData" :data="guestData" :options="chartOptions" height="180" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Bar, Line } from 'vue-chartjs'
import {
  CategoryScale,
  Chart,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  BarElement,
  Tooltip,
} from 'chart.js'

import type { AnalyticsResponse } from '@/services/api'
import { fetchAnalytics } from '@/services/api'

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Legend, Tooltip)

const analytics = ref<AnalyticsResponse | null>(null)
const loading = ref(false)

const bootstrap = async () => {
  loading.value = true
  try {
    analytics.value = await fetchAnalytics()
  } finally {
    loading.value = false
  }
}

onMounted(bootstrap)

const kpis = computed(() => {
  if (!analytics.value) {
    return [
      { label: 'Gate events', value: '—', hint: 'waiting for data' },
      { label: 'Guest sessions', value: '—', hint: '' },
      { label: 'Unpaid ratio', value: '—', hint: '' },
      { label: 'Programmes', value: '—', hint: '' },
    ]
  }
  const totalEvents = analytics.value.gate_frequency.reduce((acc, entry) => acc + entry.outer + entry.inner, 0)
  return [
    { label: 'Gate events', value: totalEvents, hint: 'last 24h' },
    { label: 'Guest sessions', value: analytics.value.guest_fee_trend.length, hint: 'completed payments' },
    { label: 'Unpaid ratio', value: Math.round(analytics.value.guest_unpaid_ratio * 100) + '%', hint: 'open guest passes' },
    { label: 'Programmes', value: Object.keys(analytics.value.programme_distribution).length, hint: 'active cohorts' },
  ]
})

const lineData = computed(() => {
  if (!analytics.value) return null
  return {
    labels: analytics.value.gate_frequency.map((entry) => new Date(entry.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Outer gate',
        data: analytics.value.gate_frequency.map((entry) => entry.outer),
        borderColor: '#38bdf8',
        backgroundColor: 'rgba(56,189,248,0.2)',
      },
      {
        label: 'Inner gate',
        data: analytics.value.gate_frequency.map((entry) => entry.inner),
        borderColor: '#c084fc',
        backgroundColor: 'rgba(192,132,252,0.2)',
      },
    ],
  }
})

const barData = computed(() => {
  if (!analytics.value) return null
  return {
    labels: Object.keys(analytics.value.role_distribution),
    datasets: [
      {
        label: 'Roles',
        backgroundColor: '#3b82f6',
        data: Object.values(analytics.value.role_distribution),
      },
      {
        label: 'Vehicles',
        backgroundColor: '#22c55e',
        data: Object.values(analytics.value.vehicle_distribution),
      },
    ],
  }
})

const guestData = computed(() => {
  if (!analytics.value) return null
  return {
    labels: analytics.value.guest_fee_trend.map((item) => new Date(item.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Fee',
        data: analytics.value.guest_fee_trend.map((item) => item.fee),
        borderColor: '#f97316',
        backgroundColor: 'rgba(249,115,22,0.2)',
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: '#cbd5f5' } },
  },
  scales: {
    x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
    y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
  },
}
</script>
