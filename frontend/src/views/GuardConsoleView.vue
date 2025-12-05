<template>
<div class="space-y-6">
    <section class="grid gap-6 lg:grid-cols-3">
      <div class="card lg:col-span-2">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm uppercase tracking-widest text-slate-400">Live Camera</p>
            <h2 class="text-xl font-semibold">Guard Console</h2>
          </div>
          <div class="flex items-center gap-2 text-sm text-slate-400">
            <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Webcam ready
          </div>
        </div>
        <div class="mt-6 aspect-video overflow-hidden rounded-2xl border border-white/5 bg-slate-900">
          <video ref="videoRef" autoplay playsinline class="h-full w-full object-cover"></video>
        </div>
        <canvas ref="canvasRef" class="hidden"></canvas>
        <div class="mt-6 flex flex-wrap gap-4">
          <select v-model="gate" class="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm">
            <option v-for="option in gateOptions" :key="option.id" :value="option.slug">
              {{ option.name }}
            </option>
          </select>
          <div class="flex items-center rounded-xl border border-white/10 text-xs">
            <button
              class="px-3 py-2 uppercase tracking-widest transition"
              :class="directionClass('entry')"
              type="button"
              @click="flowDirection = 'entry'"
            >
              Entry
            </button>
            <button
              class="px-3 py-2 uppercase tracking-widest transition"
              :class="directionClass('exit')"
              type="button"
              @click="flowDirection = 'exit'"
            >
              Exit
            </button>
          </div>
          <input
            v-model="manualPlate"
            type="text"
            placeholder="Override plate (optional)"
            class="w-52 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm uppercase tracking-widest"
          />
          <button class="btn-primary" @click="captureFrame" :disabled="guard.loading">
            {{ guard.loading ? 'Detecting…' : 'Capture & Run LPR' }}
          </button>
          <button class="rounded-xl border border-brand-400/60 px-4 py-2 text-sm" @click="verifyFace" :disabled="verifyingFace">
            {{ verifyingFace ? 'Analyzing…' : 'Face Verify' }}
          </button>
          <button class="rounded-xl border border-white/10 px-4 py-2 text-sm" @click="guard.refreshEvents">
            Refresh Events
          </button>
        </div>
        <p v-if="guard.error" class="mt-2 text-sm text-rose-400">{{ guard.error }}</p>
      </div>
      <div class="card space-y-4">
        <p class="text-sm uppercase tracking-widest text-slate-400">Decision</p>
        <div v-if="guard.latestDecision" class="space-y-4 rounded-2xl border border-white/5 bg-slate-900/60 p-4">
          <p class="text-3xl font-bold" :class="decisionColor">{{ guard.latestDecision.decision }}</p>
          <div>
            <p class="text-sm text-slate-400">Plate</p>
            <p class="text-2xl font-mono tracking-widest">{{ guard.latestDecision.plate_text }}</p>
          </div>
          <div class="grid grid-cols-2 gap-4 text-sm text-slate-300">
            <div>
              <p class="text-slate-400">Role</p>
              <p class="font-semibold">{{ guard.latestDecision.role }}</p>
            </div>
            <div>
              <p class="text-slate-400">Confidence</p>
              <p class="font-semibold">{{ guard.latestDecision.confidence }}</p>
            </div>
          </div>
          <div class="grid gap-3 text-sm text-slate-300 sm:grid-cols-2">
            <div>
              <p class="text-slate-400">Owner</p>
              <p class="font-semibold">{{ ownerDetails.name }}</p>
            </div>
            <div>
              <p class="text-slate-400">Affiliation</p>
              <p class="font-semibold">{{ ownerDetails.affiliation }}</p>
            </div>
            <div>
              <p class="text-slate-400">Phone</p>
              <p class="font-semibold">{{ ownerDetails.phone }}</p>
            </div>
            <div>
              <p class="text-slate-400">Pass status</p>
              <p :class="passStatus.expired ? 'text-rose-300' : 'text-emerald-300'">
                {{ passStatus.label }}
              </p>
            </div>
          </div>
          <p class="text-sm text-slate-400">{{ guard.latestDecision.reason }}</p>
          <button class="w-full rounded-xl border border-emerald-400/40 px-4 py-2 text-sm text-emerald-200">
            Manual Gate Override
          </button>
        </div>
        <div v-if="guard.faceMatches.length" class="rounded-2xl border border-white/5 bg-slate-900/60 p-4 text-sm">
          <p class="text-xs uppercase tracking-widest text-slate-400 mb-2">Face matches</p>
          <div v-for="match in guard.faceMatches" :key="match.user_id" class="flex items-center justify-between border-t border-white/5 py-2 first:border-t-0">
            <div>
              <p class="font-semibold text-white">{{ match.owner_name ?? match.user_id }}</p>
              <p class="text-slate-400 text-xs">{{ match.owner_affiliation ?? '—' }}</p>
            </div>
            <p class="text-brand-200 font-semibold">{{ (match.score * 100).toFixed(1) }}%</p>
          </div>
        </div>
        <div v-else class="rounded-2xl border border-dashed border-white/10 p-6 text-sm text-slate-400">
          Awaiting capture
        </div>
      </div>
    </section>

    <section class="card">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Latest entries</p>
          <h2 class="text-xl font-semibold">Access event log</h2>
        </div>
      </div>
      <div class="mt-4 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="text-left text-slate-400">
            <tr>
              <th class="pb-2 font-normal">Time</th>
              <th class="pb-2 font-normal">Plate</th>
              <th class="pb-2 font-normal">Decision</th>
              <th class="pb-2 font-normal">Gate</th>
              <th class="pb-2 font-normal">Reason</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="event in guard.events" :key="event.id" class="border-t border-white/5 text-slate-200">
              <td class="py-2 text-slate-400">{{ formatTime(event.timestamp) }}</td>
              <td class="py-2 font-mono tracking-widest">{{ event.plate_text }}</td>
              <td class="py-2">
                <span class="rounded-full px-3 py-1 text-xs font-semibold" :class="badgeClass(event.decision)">
                  {{ event.decision }}
                </span>
              </td>
              <td class="py-2 capitalize text-slate-300">{{ gateLabel(event.gate) }}</td>
              <td class="py-2 text-slate-400">{{ event.reason }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, computed } from 'vue'
import { format } from 'date-fns'

import { useGuardStore } from '@/stores/guard'
import type { AccessDecision, GateConfig } from '@/services/api'
import { fetchGates, recordParkingEvent } from '@/services/api'

const guard = useGuardStore()
const gates = ref<GateConfig[]>([])
const gate = ref<string>('outer')
const manualPlate = ref('')
const flowDirection = ref<'entry' | 'exit'>('entry')
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let mediaStream: MediaStream | null = null
const verifyingFace = ref(false)

const decisionColor = computed(() => {
  if (!guard.latestDecision) return 'text-slate-200'
  if (guard.latestDecision.decision === 'ALLOW') return 'text-emerald-400'
  if (guard.latestDecision.decision === 'DENY') return 'text-rose-400'
  return 'text-amber-300'
})

const badgeClass = (decision: string) => {
  if (decision === 'ALLOW') return 'bg-emerald-400/20 text-emerald-200'
  if (decision === 'DENY') return 'bg-rose-400/20 text-rose-200'
  return 'bg-amber-400/20 text-amber-200'
}

const directionClass = (direction: 'entry' | 'exit') =>
  direction === flowDirection.value
    ? 'bg-brand-500/20 text-brand-100'
    : 'text-slate-400 hover:text-white'

const formatTime = (iso: string) => format(new Date(iso), 'HH:mm:ss')

const gateMap = computed(() =>
  gates.value.reduce<Record<string, GateConfig>>((acc, item) => {
    acc[item.slug] = item
    return acc
  }, {})
)

const gateOptions = computed(() => gates.value.filter((option) => option.is_active))

const gateLabel = (slug: string) => gateMap.value[slug]?.name ?? slug

const ownerDetails = computed(() => {
  const decision = guard.latestDecision
  if (!decision) {
    return { name: 'Unknown driver', phone: '—', affiliation: '—' }
  }
  return {
    name: decision.owner_name ?? 'Unknown driver',
    phone: decision.owner_phone ?? '—',
    affiliation: decision.owner_affiliation ?? '—',
  }
})

const passStatus = computed(() => {
  const decision = guard.latestDecision
  if (!decision) {
    return { label: 'No data', expired: true }
  }
  if (!decision.pass_valid_to) {
    return { label: 'No pass on file', expired: true }
  }
  const expiry = new Date(decision.pass_valid_to)
  const expired = expiry.getTime() < Date.now()
  return {
    label: `${format(expiry, 'dd MMM yyyy')}${expired ? ' (expired)' : ''}`,
    expired,
  }
})

const startCamera = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
    }
  } catch (err) {
    console.error('Camera error', err)
  }
}

const captureFrame = async () => {
  if (!videoRef.value || !canvasRef.value) return
  const canvas = canvasRef.value
  const video = videoRef.value
  canvas.width = video.videoWidth || 1280
  canvas.height = video.videoHeight || 720
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const dataUrl = canvas.toDataURL('image/jpeg', 0.8)
  const [, base64Payload] = dataUrl.split(',')
  if (!base64Payload) return
  const response = await guard.capture({ gate: gate.value, plate_override: manualPlate.value || undefined, image_base64: base64Payload })
  await handleParkingEvent(response.decision)
  manualPlate.value = ''
}

const verifyFace = async () => {
  if (!videoRef.value || !canvasRef.value) return
  verifyingFace.value = true
  try {
    const canvas = canvasRef.value
    const video = videoRef.value
    canvas.width = video.videoWidth || 1280
    canvas.height = video.videoHeight || 720
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
    const [, base64Payload] = dataUrl.split(',')
    if (!base64Payload) {
      throw new Error('Unable to capture frame')
    }
    await guard.runFaceVerify(base64Payload)
  } finally {
    verifyingFace.value = false
  }
}

const loadGates = async () => {
  gates.value = await fetchGates()
  if (!gates.value.length) {
    gate.value = 'outer'
    return
  }
  const current = gateOptions.value.find((option) => option.slug === gate.value && option.is_active)
  if (!current) {
    const fallback = gateOptions.value[0] ?? gates.value[0]
    if (fallback) {
      gate.value = fallback.slug
    }
  }
}

const handleParkingEvent = async (decision: AccessDecision | null) => {
  if (!decision || decision.decision !== 'ALLOW') return
  const linkedVenue = gateMap.value[gate.value]?.parking_venue_id
  if (!linkedVenue) return
  try {
    await recordParkingEvent({ venue_id: linkedVenue, direction: flowDirection.value })
  } catch (err) {
    console.error('Parking event error', err)
  }
}

onMounted(async () => {
  await loadGates()
  await guard.refreshEvents()
  await startCamera()
})

onBeforeUnmount(() => {
  mediaStream?.getTracks().forEach((track) => track.stop())
})

</script>
