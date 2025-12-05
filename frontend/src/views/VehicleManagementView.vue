<template>
  <div class="grid gap-6 lg:grid-cols-3">
    <section class="card lg:col-span-2">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Fleet</p>
          <h2 class="text-xl font-semibold">Registered vehicles</h2>
        </div>
        <button class="rounded-xl border border-white/10 px-3 py-1 text-xs" @click="admin.reloadVehicles">
          Refresh
        </button>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="pb-2 font-normal">Plate</th>
              <th class="pb-2 font-normal">Owner</th>
              <th class="pb-2 font-normal">Role</th>
              <th class="pb-2 font-normal"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="vehicle in admin.vehicles" :key="vehicle.id" class="border-t border-white/5">
              <td class="py-2 font-mono tracking-widest">{{ vehicle.plate_text }}</td>
              <td class="py-2">{{ ownerName(vehicle.user_id) }}</td>
              <td class="py-2 text-slate-400">{{ admin.getUserById(vehicle.user_id)?.role }}</td>
              <td class="py-2 text-right">
                <button class="text-xs text-brand-300" @click="edit(vehicle)">Edit</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="card space-y-4">
      <div>
        <p class="text-sm uppercase tracking-widest text-slate-400">{{ editingId ? 'Update' : 'Create' }}</p>
        <h2 class="text-xl font-semibold">Vehicle</h2>
      </div>
      <form class="space-y-3" @submit.prevent="submit">
        <input v-model="plate" placeholder="Plate" class="form-input uppercase tracking-widest" required />
        <select v-model="userId" class="form-input" required>
          <option value="" disabled>Select owner</option>
          <option v-for="user in admin.users" :key="user.id" :value="user.id">
            {{ user.name }} · {{ user.role }}
          </option>
        </select>
        <div class="flex gap-3">
          <button class="btn-primary flex-1" type="submit">{{ editingId ? 'Save' : 'Add vehicle' }}</button>
          <button class="flex-1 rounded-xl border border-white/10 px-4 py-2" type="button" @click="reset">
            Reset
          </button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { useAdminStore } from '@/stores/admin'
import type { Vehicle } from '@/services/api'

const admin = useAdminStore()
const editingId = ref<string | null>(null)
const plate = ref('')
const userId = ref('')

const reset = () => {
  editingId.value = null
  plate.value = ''
  userId.value = ''
}

const edit = (vehicle: Vehicle) => {
  editingId.value = vehicle.id
  plate.value = vehicle.plate_text
  userId.value = vehicle.user_id
}

const submit = async () => {
  const payload = { plate_text: plate.value.toUpperCase(), user_id: userId.value }
  if (editingId.value) {
    await admin.editVehicle(editingId.value, payload)
  } else {
    await admin.addVehicle(payload)
  }
  reset()
}

const ownerName = (id: string) => admin.getUserById(id)?.name ?? 'Unknown'

onMounted(() => {
  if (!admin.vehicles.length) {
    admin.bootstrap()
  }
})
</script>

<style scoped>
.form-input {
  @apply w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm;
}
</style>
