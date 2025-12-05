import { ref } from "vue"
import { defineStore } from "pinia"

import type { GuestRate, GuestSession, Payment } from "@/services/api"
import {
  closeGuestSession,
  fetchGuestRate,
  fetchGuestSessions,
  openGuestSession,
  payGuestSession,
  updateGuestRate,
} from "@/services/api"

export const useGuestStore = defineStore("guest", () => {
  const sessions = ref<GuestSession[]>([])
  const rate = ref<GuestRate | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastPayment = ref<Payment | null>(null)

  const bootstrap = async () => {
    loading.value = true
    error.value = null
    try {
      const [sessionData, rateData] = await Promise.all([fetchGuestSessions(), fetchGuestRate()])
      sessions.value = sessionData
      rate.value = rateData
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to load guest data"
    } finally {
      loading.value = false
    }
  }

  const refreshSessions = async () => {
    sessions.value = await fetchGuestSessions()
  }

  const updateRate = async (payload: GuestRate) => {
    rate.value = await updateGuestRate(payload)
  }

  const startSession = async (plate: string) => {
    await openGuestSession(plate)
    await refreshSessions()
  }

  const stopSession = async (sessionId: string) => {
    await closeGuestSession(sessionId)
    await refreshSessions()
  }

  const paySession = async (sessionId: string, paymentSource: "touchngo" | "wallet" = "touchngo") => {
    const payment = await payGuestSession(sessionId, undefined, paymentSource)
    lastPayment.value = payment
    await refreshSessions()
  }

  return {
    sessions,
    rate,
    loading,
    error,
    lastPayment,
    bootstrap,
    refreshSessions,
    updateRate,
    startSession,
    stopSession,
    paySession,
  }
})
