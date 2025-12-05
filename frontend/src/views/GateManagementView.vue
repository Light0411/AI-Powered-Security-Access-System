<template>
  <div class="space-y-6">
    <section class="card">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Access Control</p>
          <h2 class="text-xl font-semibold">Gates & Role Thresholds</h2>
        </div>
        <div class="flex gap-2">
          <button class="rounded-xl border border-white/15 px-4 py-2 text-sm" @click="resetGateForm">New Gate</button>
          <button class="rounded-xl border border-white/15 px-4 py-2 text-sm" @click="resetVenueForm">New Venue</button>
        </div>
      </div>
      <div class="mt-6 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="pb-2 font-normal">Name</th>
              <th class="pb-2 font-normal">Slug</th>
              <th class="pb-2 font-normal">Min Role</th>
              <th class="pb-2 font-normal">Venue</th>
              <th class="pb-2 font-normal">Flow</th>
              <th class="pb-2 font-normal">Location</th>
              <th class="pb-2 font-normal">Active</th>
              <th class="pb-2 font-normal text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="gate in gates" :key="gate.id" class="border-t border-white/5 text-slate-200">
              <td class="py-3 font-medium">{{ gate.name }}</td>
              <td class="py-3 text-slate-400 font-mono text-xs uppercase">{{ gate.slug }}</td>
              <td class="py-3 capitalize">{{ gate.min_role }}</td>
              <td class="py-3 text-slate-400">{{ venueLabel(gate.parking_venue_id) }}</td>
              <td class="py-3 text-slate-400">{{ gate.parking_direction ?? '—' }}</td>
              <td class="py-3 text-slate-400">{{ gate.location || '—' }}</td>
              <td class="py-3">
                <span
                  class="rounded-full px-3 py-1 text-xs font-semibold"
                  :class="gate.is_active ? 'bg-emerald-400/20 text-emerald-200' : 'bg-slate-600/30 text-slate-300'"
                >
                  {{ gate.is_active ? 'Active' : 'Disabled' }}
                </span>
              </td>
              <td class="py-3 text-right">
                <div class="flex justify-end gap-2">
                  <button class="text-xs text-brand-200 hover:underline" @click="editGate(gate)">Edit</button>
                  <button class="text-xs text-rose-300 hover:underline" @click="removeGate(gate.id)">Delete</button>
                </div>
              </td>
            </tr>
            <tr v-if="!gates.length">
              <td class="py-6 text-center text-slate-500" colspan="8">No gates configured yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div class="grid gap-6 lg:grid-cols-2">
      <section class="card space-y-4">
        <h3 class="text-lg font-semibold">{{ gateEditingId ? 'Edit Gate' : 'Create Gate' }}</h3>
        <form class="grid gap-4" @submit.prevent="submitGate">
          <div class="grid gap-4 md:grid-cols-2">
            <label class="text-sm text-slate-400">
              Name
              <input v-model="gateForm.name" class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white" required />
            </label>
            <label class="text-sm text-slate-400">
              Slug
              <input
                v-model="gateForm.slug"
                class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs uppercase text-white"
                required
                pattern="^[a-z0-9\\-]+$"
                title="Lowercase letters, numbers, and hyphens only"
              />
            </label>
            <label class="text-sm text-slate-400">
              Location (optional)
              <input
                v-model="gateForm.location"
                class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white"
                placeholder="North perimeter"
              />
            </label>
            <label class="text-sm text-slate-400">
              Minimum role
              <select
                v-model="gateForm.min_role"
                class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
              >
                <option v-for="role in roles" :key="role" :value="role">{{ role }}</option>
              </select>
            </label>
          </div>
          <label class="text-sm text-slate-400">
            Track venue occupancy
            <select
              v-model="gateForm.parking_venue_id"
              class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
            >
              <option value="">Not linked</option>
              <option v-for="venue in venues" :key="venue.id" :value="venue.id">
                {{ venue.name }} ({{ venue.capacity }} slots)
              </option>
            </select>
          </label>
          <label class="text-sm text-slate-400">
            Flow direction
            <select
              v-model="gateForm.parking_direction"
              class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white"
              :disabled="!gateForm.parking_venue_id"
            >
              <option value="">Not set</option>
              <option value="entry">Entry</option>
              <option value="exit">Exit</option>
            </select>
          </label>
          <label class="flex items-center gap-2 text-sm text-slate-400">
            <input v-model="gateForm.is_active" type="checkbox" class="rounded border-white/30 bg-white/5" />
            Gate is active
          </label>
          <div class="flex justify-end gap-3">
            <button type="button" class="rounded-xl border border-white/10 px-4 py-2 text-sm" @click="resetGateForm">Cancel</button>
            <button type="submit" class="btn-primary">{{ gateEditingId ? 'Save changes' : 'Add gate' }}</button>
          </div>
        </form>
      </section>

      <section class="card space-y-4">
        <h3 class="text-lg font-semibold">{{ venueEditingId ? 'Edit Venue' : 'Create Venue' }}</h3>
        <form class="grid gap-4" @submit.prevent="submitVenue">
          <label class="text-sm text-slate-400">
            Venue name
            <input
              v-model="venueForm.name"
              class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white"
              placeholder="North Deck"
              required
            />
          </label>
          <div class="grid gap-4 md:grid-cols-2">
            <label class="text-sm text-slate-400">
              Capacity
              <input
                v-model.number="venueForm.capacity"
                type="number"
                min="0"
                class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white"
                required
              />
            </label>
            <label class="text-sm text-slate-400">
              Occupied
              <input
                v-model.number="venueForm.occupied"
                type="number"
                min="0"
                class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white"
              />
            </label>
          </div>
          <div class="flex justify-end gap-3">
            <button type="button" class="rounded-xl border border-white/10 px-4 py-2 text-sm" @click="resetVenueForm">Cancel</button>
            <button type="submit" class="btn-primary">{{ venueEditingId ? 'Save venue' : 'Add venue' }}</button>
          </div>
        </form>
      </section>
    </div>

    <section class="card">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Parking Venues</p>
          <h3 class="text-lg font-semibold">Tracked lots</h3>
        </div>
        <button class="rounded-xl border border-white/15 px-4 py-2 text-sm" @click="resetVenueForm">Create Venue</button>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="pb-2 font-normal">Name</th>
              <th class="pb-2 font-normal">Capacity</th>
              <th class="pb-2 font-normal">Occupied</th>
              <th class="pb-2 font-normal">Percent</th>
              <th class="pb-2 font-normal text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="venue in venues" :key="venue.id" class="border-t border-white/5 text-slate-200">
              <td class="py-3 font-medium">{{ venue.name }}</td>
              <td class="py-3 text-slate-400">{{ venue.capacity }}</td>
              <td class="py-3 text-slate-400">{{ venue.occupied }}</td>
              <td class="py-3 text-slate-400">{{ venue.percent.toFixed(1) }}%</td>
              <td class="py-3 text-right">
                <div class="flex justify-end gap-2">
                  <button class="text-xs text-brand-200 hover:underline" @click="editVenue(venue)">Edit</button>
                  <button class="text-xs text-rose-300 hover:underline" @click="removeVenue(venue.id)">Delete</button>
                </div>
              </td>
            </tr>
            <tr v-if="!venues.length">
              <td class="py-6 text-center text-slate-500" colspan="5">No venues tracked yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import type { GateConfig, ParkingVenuePayload, ParkingVenueStatus, Role } from '@/services/api'
import {
  createGate,
  createParkingVenue,
  deleteGate,
  deleteParkingVenue,
  fetchGates,
  fetchParkingVenues,
  updateGate,
  updateParkingVenue,
} from '@/services/api'

const gates = ref<GateConfig[]>([])
const venues = ref<ParkingVenueStatus[]>([])
const gateEditingId = ref<string | null>(null)
const venueEditingId = ref<string | null>(null)
const roles: Role[] = ['guest', 'student', 'staff', 'security', 'admin']

const gateForm = reactive({
  name: '',
  slug: '',
  min_role: 'guest' as Role,
  location: '',
  is_active: true,
  parking_venue_id: '',
  parking_direction: '' as '' | 'entry' | 'exit',
})

const venueForm = reactive({
  name: '',
  capacity: 0,
  occupied: 0,
})

const venueMap = computed(() =>
  venues.value.reduce<Record<string, ParkingVenueStatus>>((acc, venue) => {
    acc[venue.id] = venue
    return acc
  }, {})
)

const venueLabel = (venueId?: string | null) => {
  if (!venueId) return '—'
  return venueMap.value[venueId]?.name ?? venueId
}

const loadGates = async () => {
  gates.value = await fetchGates()
}

const loadVenues = async () => {
  venues.value = await fetchParkingVenues()
  if (gateForm.parking_venue_id && !venueMap.value[gateForm.parking_venue_id]) {
    gateForm.parking_venue_id = ''
    gateForm.parking_direction = ''
  }
}

const resetGateForm = () => {
  gateEditingId.value = null
  gateForm.name = ''
  gateForm.slug = ''
  gateForm.location = ''
  gateForm.min_role = 'guest'
  gateForm.is_active = true
  gateForm.parking_venue_id = ''
  gateForm.parking_direction = ''
}

const resetVenueForm = () => {
  venueEditingId.value = null
  venueForm.name = ''
  venueForm.capacity = 0
  venueForm.occupied = 0
}

const editGate = (gate: GateConfig) => {
  gateEditingId.value = gate.id
  gateForm.name = gate.name
  gateForm.slug = gate.slug
  gateForm.location = gate.location ?? ''
  gateForm.min_role = gate.min_role
  gateForm.is_active = gate.is_active
  gateForm.parking_venue_id = gate.parking_venue_id ?? ''
  gateForm.parking_direction = gate.parking_direction ?? ''
}

const editVenue = (venue: ParkingVenueStatus) => {
  venueEditingId.value = venue.id
  venueForm.name = venue.name
  venueForm.capacity = venue.capacity
  venueForm.occupied = venue.occupied
}

const submitGate = async () => {
  const payload = {
    name: gateForm.name,
    slug: gateForm.slug,
    location: NoneIfEmpty(gateForm.location),
    min_role: gateForm.min_role,
    is_active: gateForm.is_active,
    parking_venue_id: gateForm.parking_venue_id || null,
    parking_direction: gateForm.parking_direction ? gateForm.parking_direction : null,
  }
  if (gateEditingId.value) {
    await updateGate(gateEditingId.value, payload)
  } else {
    await createGate(payload)
  }
  await loadGates()
  resetGateForm()
}

const submitVenue = async () => {
  const payload: ParkingVenuePayload = {
    name: venueForm.name,
    capacity: venueForm.capacity,
    occupied: venueForm.occupied ?? 0,
  }
  if (venueEditingId.value) {
    await updateParkingVenue(venueEditingId.value, payload)
  } else {
    await createParkingVenue(payload)
  }
  await loadVenues()
  await loadGates()
  resetVenueForm()
}

const removeGate = async (id: string) => {
  if (!confirm('Delete this gate?')) return
  await deleteGate(id)
  await loadGates()
}

const removeVenue = async (id: string) => {
  if (!confirm('Delete this venue? Gates linked to it will be unassigned.')) return
  await deleteParkingVenue(id)
  await loadVenues()
  await loadGates()
  if (venueEditingId.value === id) {
    resetVenueForm()
  }
}

watch(
  () => gateForm.parking_venue_id,
  (val) => {
    if (!val) {
      gateForm.parking_direction = ''
    }
  }
)

function NoneIfEmpty(value?: string | null): string | null {
  if (!value) return null
  const trimmed = value.trim()
  return trimmed.length ? trimmed : null
}

loadVenues().then(() => loadGates())
</script>
