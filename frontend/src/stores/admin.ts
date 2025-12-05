import { computed, ref } from "vue"
import { defineStore } from "pinia"

import type {
  Pass,
  PassApplication,
  PassApplicationDecisionPayload,
  PassIssuePayload,
  PassPlan,
  PassUpdatePayload,
  User,
  Vehicle,
} from "@/services/api"
import {
  createPass,
  createUser,
  createVehicle,
  deletePass,
  deleteUser,
  deleteVehicle,
  fetchPassPlans,
  fetchPassApplications,
  fetchPasses,
  fetchUsers,
  fetchVehicles,
  reviewPassApplication,
  updatePass,
  updateUser,
  updateVehicle,
} from "@/services/api"

export const useAdminStore = defineStore("admin", () => {
  const users = ref<User[]>([])
  const vehicles = ref<Vehicle[]>([])
  const passes = ref<Pass[]>([])
  const passPlans = ref<PassPlan[]>([])
  const passApplications = ref<PassApplication[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const userLookup = computed(() => Object.fromEntries(users.value.map((user) => [user.id, user])))

  const bootstrap = async () => {
    loading.value = true
    error.value = null
    try {
      const [userData, vehicleData, passData, planData, applicationData] = await Promise.all([
        fetchUsers(),
        fetchVehicles(),
        fetchPasses(),
        fetchPassPlans(),
        fetchPassApplications(),
      ])
      users.value = userData
      vehicles.value = vehicleData
      passes.value = passData
      passPlans.value = planData
      passApplications.value = applicationData
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to load admin data"
    } finally {
      loading.value = false
    }
  }

  const reloadUsers = async () => {
    users.value = await fetchUsers()
  }

  const reloadVehicles = async () => {
    vehicles.value = await fetchVehicles()
  }

  const reloadPasses = async () => {
    passes.value = await fetchPasses()
  }

  const reloadPassApplications = async (status?: string) => {
    passApplications.value = await fetchPassApplications(status)
  }

  const loadPassPlans = async () => {
    passPlans.value = await fetchPassPlans()
  }

  const addUser = async (payload: Partial<User>) => {
    const created = await createUser(payload)
    users.value = [...users.value, created]
  }

  const editUser = async (id: string, payload: Partial<User>) => {
    const updated = await updateUser(id, payload)
    users.value = users.value.map((user) => (user.id === id ? updated : user))
  }

  const removeUser = async (id: string) => {
    await deleteUser(id)
    users.value = users.value.filter((user) => user.id !== id)
  }

  const addVehicle = async (payload: Partial<Vehicle>) => {
    const created = await createVehicle(payload)
    vehicles.value = [...vehicles.value, created]
  }

  const editVehicle = async (id: string, payload: Partial<Vehicle>) => {
    const updated = await updateVehicle(id, payload)
    vehicles.value = vehicles.value.map((vehicle) => (vehicle.id === id ? updated : vehicle))
  }

  const removeVehicle = async (id: string) => {
    await deleteVehicle(id)
    vehicles.value = vehicles.value.filter((vehicle) => vehicle.id !== id)
  }

  const addPass = async (payload: PassIssuePayload) => {
    const created = await createPass(payload)
    passes.value = [...passes.value, created]
  }

  const editPass = async (id: string, payload: PassUpdatePayload) => {
    const updated = await updatePass(id, payload)
    passes.value = passes.value.map((item) => (item.id === id ? updated : item))
  }

  const removePass = async (id: string) => {
    await deletePass(id)
    passes.value = passes.value.filter((item) => item.id !== id)
  }

  const getUserById = (id: string) => userLookup.value[id] ?? null

  const reviewApplication = async (id: string, payload: PassApplicationDecisionPayload) => {
    await reviewPassApplication(id, payload)
    await Promise.all([reloadPassApplications(), reloadPasses()])
  }

  return {
    users,
    vehicles,
    passes,
    passPlans,
    passApplications,
    loading,
    error,
    get userMap() {
      return userLookup.value
    },
    getUserById,
    bootstrap,
    reloadUsers,
    reloadVehicles,
    reloadPasses,
    reloadPassApplications,
    loadPassPlans,
    addUser,
    editUser,
    removeUser,
    addVehicle,
    editVehicle,
    removeVehicle,
    addPass,
    editPass,
    removePass,
    reviewApplication,
  }
})
