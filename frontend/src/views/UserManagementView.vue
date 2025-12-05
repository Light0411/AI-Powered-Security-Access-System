<template>
  <div class="grid gap-6 lg:grid-cols-3">
    <section class="card lg:col-span-2">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Directory</p>
          <h2 class="text-xl font-semibold">Registered users</h2>
        </div>
        <button class="rounded-xl border border-white/10 px-3 py-1 text-xs" @click="admin.reloadUsers">
          Refresh
        </button>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="pb-2 font-normal">Name</th>
              <th class="pb-2 font-normal">Role</th>
              <th class="pb-2 font-normal">Programme</th>
              <th class="pb-2 font-normal">Phone</th>
              <th class="pb-2 font-normal text-right">Wallet</th>
              <th class="pb-2 font-normal"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in admin.users" :key="user.id" class="border-t border-white/5">
              <td class="py-2 font-medium">{{ user.name }}</td>
              <td class="py-2 capitalize">{{ user.role }}</td>
              <td class="py-2 text-slate-400">{{ user.programme }}</td>
              <td class="py-2 text-slate-400">{{ user.phone }}</td>
              <td class="py-2 text-right font-mono text-emerald-300">
                RM {{ (user.wallet_balance ?? 0).toFixed(2) }}
              </td>
              <td class="py-2 text-right">
                <button class="text-xs text-brand-300" @click="edit(user)">Edit</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="card space-y-4">
      <div>
        <p class="text-sm uppercase tracking-widest text-slate-400">{{ editingId ? 'Update' : 'Create' }}</p>
        <h2 class="text-xl font-semibold">User record</h2>
      </div>
      <form class="space-y-3" @submit.prevent="submit">
        <input v-model="form.name" placeholder="Full name" class="form-input" required />
        <input v-model="form.email" type="email" placeholder="Email" class="form-input" required />
        <input v-model="form.phone" placeholder="Phone" class="form-input" required />
        <input v-model="form.programme" placeholder="Programme" class="form-input" required />
        <select v-model="form.role" class="form-input" required>
          <option value="student">Student</option>
          <option value="staff">Staff</option>
          <option value="security">Security</option>
          <option value="admin">Admin</option>
        </select>
        <div class="flex gap-3">
          <button class="btn-primary flex-1" type="submit">{{ editingId ? 'Save changes' : 'Add user' }}</button>
          <button class="flex-1 rounded-xl border border-white/10 px-4 py-2" type="button" @click="reset">
            Reset
          </button>
        </div>
      </form>
      <p v-if="admin.error" class="text-xs text-rose-400">{{ admin.error }}</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { useAdminStore } from '@/stores/admin'
import type { User } from '@/services/api'

const admin = useAdminStore()
const editingId = ref<string | null>(null)
const form = reactive<Partial<User>>({
  name: '',
  email: '',
  phone: '',
  role: 'student',
  programme: '',
})

const reset = () => {
  editingId.value = null
  form.name = ''
  form.email = ''
  form.phone = ''
  form.programme = ''
  form.role = 'student'
}

const edit = (user: User) => {
  editingId.value = user.id
  form.name = user.name
  form.email = user.email
  form.phone = user.phone
  form.programme = user.programme
  form.role = user.role
}

const submit = async () => {
  if (editingId.value) {
    await admin.editUser(editingId.value, form)
  } else {
    await admin.addUser(form)
  }
  reset()
}

onMounted(() => {
  if (!admin.users.length) {
    admin.bootstrap()
  }
})
</script>

<style scoped>
.form-input {
  @apply w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm;
}
</style>
