import { ref } from "vue"
import { defineStore } from "pinia"

import type { AccessDecision, AccessEvent, FaceMatch } from "@/services/api"
import { fetchAccessEvents, runInference, verifyFace } from "@/services/api"

export const useGuardStore = defineStore("guard", () => {
  const latestDecision = ref<AccessDecision | null>(null)
  const events = ref<AccessEvent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const faceMatches = ref<FaceMatch[]>([])

  const capture = async (payload: { gate: string; plate_override?: string; image_base64?: string }) => {
    loading.value = true
    error.value = null
    try {
      const response = await runInference(payload)
      latestDecision.value = response.decision
      events.value = [response.event, ...events.value].slice(0, 10)
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Could not run inference"
      throw err
    } finally {
      loading.value = false
    }
  }

  const runFaceVerify = async (image_base64: string) => {
    faceMatches.value = []
    try {
      const response = await verifyFace({ image_base64 })
      faceMatches.value = response.matches
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Face verification failed"
      throw err
    }
  }

  const refreshEvents = async () => {
    events.value = await fetchAccessEvents(20)
  }

  return { latestDecision, events, loading, error, faceMatches, capture, refreshEvents, runFaceVerify }
})
