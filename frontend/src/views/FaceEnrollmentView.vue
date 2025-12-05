<template>
  <div class="grid gap-6 lg:grid-cols-3">
    <section class="card space-y-4">
      <div>
        <p class="text-sm uppercase tracking-widest text-slate-400">Face enrollment</p>
        <h2 class="text-xl font-semibold">Capture profile</h2>
      </div>
      <label class="text-sm text-slate-400">
        Select user
        <select v-model="selectedUser" class="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm" required>
          <option value="">Choose user</option>
          <option v-for="user in admin.users" :key="user.id" :value="user.id">
            {{ user.name }} · {{ user.role }}
          </option>
        </select>
      </label>
      <div class="rounded-2xl border border-white/5 bg-slate-900">
        <video ref="videoRef" autoplay playsinline class="h-64 w-full rounded-2xl object-cover"></video>
      </div>
      <canvas ref="canvasRef" class="hidden"></canvas>
      <button class="btn-primary w-full" :disabled="!selectedUser || submitting" @click="captureFace">
        {{ submitting ? 'Enrolling…' : 'Capture & Enroll' }}
      </button>
      <p v-if="message" class="text-sm text-emerald-300">{{ message }}</p>
      <p v-if="error" class="text-sm text-rose-400">{{ error }}</p>
    </section>
    <section class="card lg:col-span-2">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm uppercase tracking-widest text-slate-400">Profiles</p>
          <h2 class="text-xl font-semibold">Recent enrollments</h2>
        </div>
        <button class="rounded-xl border border-white/10 px-3 py-1 text-xs" @click="loadProfiles">Refresh</button>
      </div>
      <div class="mt-4 space-y-3 text-sm">
        <div
          v-for="profile in profiles"
          :key="profile.id"
          class="rounded-2xl border border-white/5 bg-slate-900/40 p-4 flex items-center justify-between"
        >
          <div>
            <p class="text-white font-semibold">{{ admin.getUserById(profile.user_id)?.name ?? profile.user_id }}</p>
            <p class="text-slate-400 text-xs">{{ formatTime(profile.captured_at) }}</p>
          </div>
          <p class="text-xs text-slate-400 font-mono">{{ profile.id }}</p>
        </div>
        <p v-if="!profiles.length" class="text-slate-400 text-sm">No faces enrolled yet.</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns'
import { onBeforeUnmount, onMounted, ref } from 'vue'

import type { UserFace } from '@/services/api'
import { enrollFace, fetchFaceProfiles } from '@/services/api'
import { useAdminStore } from '@/stores/admin'

const admin = useAdminStore()
const selectedUser = ref('')
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const submitting = ref(false)
const message = ref('')
const error = ref('')
const profiles = ref<UserFace[]>([])
let mediaStream: MediaStream | null = null

const startCamera = async () => {
  mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
  if (videoRef.value) {
    videoRef.value.srcObject = mediaStream
  }
}

const captureFace = async () => {
  if (!videoRef.value || !canvasRef.value || !selectedUser.value) return
  message.value = ''
  error.value = ''
  submitting.value = true
  try {
    const canvas = canvasRef.value
    const video = videoRef.value
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
    const [, base64Payload] = dataUrl.split(',')
    if (!base64Payload) {
      throw new Error('Unable to capture frame')
    }
    const response = await enrollFace({ user_id: selectedUser.value, image_base64: base64Payload })
    const enrolledUser = admin.getUserById(response.profile.user_id)
    message.value = `Face saved for ${enrolledUser?.name ?? response.profile.user_id}`
    await loadProfiles()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to enroll face'
  } finally {
    submitting.value = false
  }
}

const loadProfiles = async () => {
  const data = await fetchFaceProfiles()
  profiles.value = [...data].sort(
    (a, b) => new Date(b.captured_at).getTime() - new Date(a.captured_at).getTime(),
  )
}

const formatTime = (iso: string) => format(new Date(iso), 'dd MMM yyyy, HH:mm')

onMounted(async () => {
  if (!admin.users.length) {
    await admin.reloadUsers()
  }
  await loadProfiles()
  await startCamera()
})

onBeforeUnmount(() => {
  mediaStream?.getTracks().forEach((track) => track.stop())
})
</script>
