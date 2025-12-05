<template>
  <div class="min-h-screen bg-slate-950 text-slate-100">
    <div class="flex min-h-screen">
      <aside class="hidden w-64 border-r border-white/5 bg-slate-950/70 px-6 py-8 lg:block">
        <div class="mb-10 flex items-center gap-2 text-xl font-semibold tracking-wide">
          <span class="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-600/20 text-brand-400">SG</span>
          SmartGate
        </div>
        <nav class="space-y-2 text-sm">
          <RouterLink
            v-for="item in menu"
            :key="item.to"
            :to="item.to"
            class="flex items-center gap-3 rounded-xl px-4 py-2 font-medium transition-colors"
            :class="route.path.startsWith(item.to) ? 'bg-brand-500/20 text-white' : 'text-slate-400 hover:bg-white/5'"
          >
            <component :is="item.icon" class="h-5 w-5" />
            {{ item.label }}
          </RouterLink>
        </nav>
        <div class="mt-16 rounded-2xl border border-white/5 bg-slate-900/40 p-4 text-xs text-slate-400">
          <p class="font-semibold text-white">Laptop Demo</p>
          <p>Version 0.2.0 · Mock Inference</p>
          <p>Supabase ready</p>
        </div>
      </aside>
      <main class="flex-1">
        <header class="sticky top-0 z-10 border-b border-white/5 bg-slate-950/80 px-6 py-4 backdrop-blur">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-widest text-slate-400">SmartGate LPR Prototype</p>
              <h1 class="text-xl font-semibold text-white">{{ currentTitle }}</h1>
            </div>
            <RouterLink
              to="/portal/mypass"
              class="rounded-full border border-brand-500/50 px-4 py-2 text-sm font-medium text-brand-100"
            >
              My Pass Portal
            </RouterLink>
          </div>
        </header>
        <div class="px-4 py-6 sm:px-6 lg:px-10">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChartBarIcon,
  ShieldCheckIcon,
  UsersIcon,
  TicketIcon,
  Squares2X2Icon,
  CreditCardIcon,
  UserCircleIcon,
  MapPinIcon,
  FaceSmileIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()

const menu = [
  { label: 'Guard Console', to: '/guard', icon: ShieldCheckIcon },
  { label: 'Admin Dashboard', to: '/admin/dashboard', icon: ChartBarIcon },
  { label: 'Users', to: '/admin/users', icon: UsersIcon },
  { label: 'Vehicles', to: '/admin/vehicles', icon: Squares2X2Icon },
  { label: 'Passes', to: '/admin/passes', icon: TicketIcon },
  { label: 'Gates', to: '/admin/gates', icon: MapPinIcon },
  { label: 'Face Enroll', to: '/admin/face', icon: FaceSmileIcon },
  { label: 'Guest Mgmt', to: '/admin/guest', icon: CreditCardIcon },
  { label: 'Role Upgrades', to: '/admin/upgrades', icon: ArrowTrendingUpIcon },
  { label: 'My Pass', to: '/portal/mypass', icon: UserCircleIcon },
]

const currentTitle = computed(() => route.meta.title ?? 'Command Center')
</script>
