<template>
  <div class="space-y-6">
    <section class="card">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Pending requests</p>
          <h2 class="text-xl font-semibold">Role upgrades</h2>
        </div>
        <button class="rounded-xl border border-white/10 px-3 py-1 text-xs" @click="loadUpgrades" :disabled="loading">
          {{ loading ? 'Refreshing…' : 'Refresh' }}
        </button>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="pb-2 font-normal">User</th>
              <th class="pb-2 font-normal">Target role</th>
              <th class="pb-2 font-normal">Reason</th>
              <th class="pb-2 font-normal">Submitted</th>
              <th class="pb-2 font-normal text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="request in upgrades" :key="request.id" class="border-t border-white/5">
              <td class="py-3">
                <p class="font-semibold text-white">{{ userName(request.user_id) }}</p>
                <p class="text-xs text-slate-400">{{ request.user_id }}</p>
              </td>
              <td class="py-3 capitalize text-slate-300">{{ request.target_role }}</td>
              <td class="py-3 max-w-sm text-slate-400">{{ request.reason }}</td>
              <td class="py-3 text-slate-400">{{ formatDate(request.submitted_at) }}</td>
              <td class="py-3 text-right space-x-2">
                <button class="rounded-xl border border-emerald-400/60 px-3 py-1 text-xs text-emerald-200" @click="decide(request, 'approved')" :disabled="!reviewerId">
                  Approve
                </button>
                <button class="rounded-xl border border-rose-400/60 px-3 py-1 text-xs text-rose-200" @click="decide(request, 'rejected')" :disabled="!reviewerId">
                  Reject
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!upgrades.length && !loading" class="py-6 text-center text-sm text-slate-500">No pending upgrades.</p>
      </div>
      <p v-if="!reviewerId" class="mt-4 text-xs text-amber-300">
        Add an admin user to approve requests. No reviewer found in the current user list.
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns'
import { onMounted, ref, computed } from 'vue'

import { useAdminStore } from '@/stores/admin'
import type { RoleUpgradeRequest } from '@/services/api'
import { fetchRoleUpgrades, reviewRoleUpgrade } from '@/services/api'

const admin = useAdminStore()
const upgrades = ref<RoleUpgradeRequest[]>([])
const loading = ref(false)

const reviewerId = computed(() => admin.users.find((user) => user.role === 'admin')?.id ?? admin.users[0]?.id ?? '')

const loadUpgrades = async () => {
  loading.value = true
  try {
    upgrades.value = await fetchRoleUpgrades('pending')
  } finally {
    loading.value = false
  }
}

const decide = async (request: RoleUpgradeRequest, status: 'approved' | 'rejected') => {
  if (!reviewerId.value) return
  const updated = await reviewRoleUpgrade(request.id, { status, reviewer_id: reviewerId.value })
  upgrades.value = upgrades.value.filter((item) => item.id !== updated.id)
}

const userName = (userId: string) => admin.getUserById(userId)?.name ?? 'Unknown user'
const formatDate = (iso: string) => format(new Date(iso), 'dd MMM yyyy HH:mm')

onMounted(async () => {
  if (!admin.users.length) {
    await admin.bootstrap()
  }
  await loadUpgrades()
})
</script>
