import axios from "axios"

export type Role = "guest" | "student" | "staff" | "security" | "admin"

export interface GateConfig {
  id: string
  name: string
  slug: string
  min_role: Role
  location?: string | null
  is_active: boolean
  parking_venue_id?: string | null
  parking_direction?: "entry" | "exit" | null
}

// Allow slower YOLO/EasyOCR warmups when the real pipeline is enabled.
const REQUEST_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT ?? 45000) || 45000

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? "http://localhost:60000/api",
  timeout: REQUEST_TIMEOUT,
})

export interface User {
  id: string
  name: string
  email: string
  phone: string
  role: Role
  programme: string
  wallet_balance?: number
}

export interface Vehicle {
  id: string
  plate_text: string
  user_id: string
}

export type PassPlanType = "short_semester" | "long_semester" | "annual"

export interface Pass {
  id: string
  user_id: string
  role: Role
  plan_type: PassPlanType
  valid_from: string
  valid_to: string
  price_rm: number
  is_paid: boolean
  paid_at?: string | null
}

export interface PassApplication {
  id: string
  user_id: string
  role: Role
  plan_type: PassPlanType
  vehicles: string[]
  status: "pending" | "approved" | "rejected"
  reviewer_id?: string | null
  review_note?: string | null
  submitted_at: string
  reviewed_at?: string | null
}

export interface PassApplicationDecisionPayload {
  status: "approved" | "rejected"
  reviewer_id: string
  note?: string
}

export interface PassPlan {
  plan_type: PassPlanType
  label: string
  duration_days: number
  price_rm: number
}

export interface PassIssuePayload {
  user_id: string
  role: Role
  plan_type: PassPlanType
  starts_at?: string
}

export interface PassUpdatePayload {
  role?: Role
  plan_type?: PassPlanType
  starts_at?: string
}

export interface UserFace {
  id: string
  user_id: string
  embedding: number[]
  captured_at: string
}

export interface AccessEvent {
  id: string
  plate_text: string
  confidence: number
  decision: "ALLOW" | "DENY" | "GUEST"
  role: Role
  reason: string
  gate: string
  timestamp: string
}

export interface AccessDecision {
  plate_text: string
  confidence: number
  decision: "ALLOW" | "DENY" | "GUEST"
  role: Role
  reason: string
  gate: string
  owner_name?: string | null
  owner_phone?: string | null
  owner_affiliation?: string | null
  pass_valid_to?: string | null
}

export interface APIMessage {
  message: string
}

export interface InferenceResponse {
  decision: AccessDecision
  event: AccessEvent
}

export interface GuestSession {
  id: string
  plate_text: string
  start_time: string
  end_time?: string
  minutes?: number
  fee?: number
  status: "open" | "closed" | "paid"
}

export interface GuestRate {
  base_rate: number
  per_minute_rate: number
}

export interface Payment {
  id: string
  amount: number
  status: "pending" | "succeeded" | "failed"
  processor: string
  timestamp: string
  currency: string
  session_id?: string | null
  pass_id?: string | null
  reference?: string | null
}

export interface WalletTransaction {
  id: string
  user_id: string
  amount: number
  type: "top_up" | "debit" | "guest_payment" | "refund" | "pass_payment"
  description: string
  timestamp: string
  source: string
}

export interface ClientProfile {
  user_id: string
  registration_id: string
  status: "pending" | "active" | "suspended"
  guest_pin: string
  wallet_balance: number
  created_at: string
  updated_at: string
}

export interface ClientWallet {
  user_id: string
  balance: number
  currency: string
  last_top_up?: string | null
}

export interface ClientWalletActivity {
  wallet: ClientWallet
  transactions: WalletTransaction[]
}

export interface WalletTopUpRequest {
  amount: number
  source?: string
}

export interface RoleUpgradeRequest {
  id: string
  user_id: string
  target_role: Role
  reason: string
  attachments: string[]
  status: "pending" | "approved" | "rejected"
  submitted_at: string
  reviewed_at?: string | null
}

export interface RoleUpgradeSubmit {
  target_role: Role
  reason: string
  attachments?: string[]
}

export interface ClientRegistrationRequest {
  name: string
  email: string
  phone: string
  programme: string
  role: Role
  plan_type: PassPlanType
  vehicles: string[]
}

export interface ClientRegistrationResponse {
  registration: {
    id: string
    user_id: string
    status: "pending" | "active" | "suspended"
    submitted_at: string
  }
  profile: ClientProfile
  user: User
  pass_info?: Pass | null
  vehicles: Vehicle[]
  pass_application: PassApplication
}

export interface ClientSummary {
  user: User
  pass_info?: Pass | null
  vehicles: Vehicle[]
  profile: ClientProfile
  wallet: ClientWallet
  guest_sessions: GuestSession[]
  role_upgrades: RoleUpgradeRequest[]
  pass_applications: PassApplication[]
}

export interface GuestSessionLookupResponse {
  session: GuestSession
  amount_due: number
}

export interface ClientGuestPaymentRequest {
  session_id: string
  amount?: number
  payment_source: "touchngo" | "wallet"
  user_id?: string
}

export interface ParkingVenueStatus {
  id: string
  name: string
  capacity: number
  occupied: number
  percent: number
}

export interface ParkingOverview {
  venues: ParkingVenueStatus[]
}

export interface ParkingVenuePayload {
  id?: string
  name: string
  capacity: number
  occupied?: number
}

export interface Notification {
  id: string
  user_id: string
  message: string
  created_at: string
  is_read: boolean
}

export interface RoleUpgradeDecisionPayload {
  status: "approved" | "rejected"
  reviewer_id: string
  note?: string
}

export interface AnalyticsResponse {
  gate_frequency: Array<{ timestamp: string; outer: number; inner: number }>
  guest_fee_trend: Array<{ timestamp: string; fee: number }>
  role_distribution: Record<string, number>
  programme_distribution: Record<string, number>
  guest_unpaid_ratio: number
  vehicle_distribution: Record<string, number>
}

export interface FaceMatch {
  user_id: string
  score: number
  owner_name?: string | null
  owner_phone?: string | null
  owner_affiliation?: string | null
}

export interface FaceVerifyResponse {
  matches: FaceMatch[]
}

export interface FaceEnrollResponse {
  message: string
  profile: UserFace
}

const unwrap = <T>(promise: Promise<{ data: T }>) => promise.then((r) => r.data)

export const fetchUsers = () => unwrap<User[]>(api.get("/admin/users"))
export const createUser = (payload: Partial<User>) => unwrap<User>(api.post("/admin/users", payload))
export const updateUser = (id: string, payload: Partial<User>) => unwrap<User>(api.put("/admin/users/" + id, payload))
export const deleteUser = (id: string) => unwrap(api.delete("/admin/users/" + id))

export const fetchVehicles = () => unwrap<Vehicle[]>(api.get("/admin/vehicles"))
export const createVehicle = (payload: Partial<Vehicle>) => unwrap<Vehicle>(api.post("/admin/vehicles", payload))
export const updateVehicle = (id: string, payload: Partial<Vehicle>) => unwrap<Vehicle>(api.put("/admin/vehicles/" + id, payload))
export const deleteVehicle = (id: string) => unwrap(api.delete("/admin/vehicles/" + id))

export const fetchPasses = () => unwrap<Pass[]>(api.get("/admin/passes"))
export const fetchPassPlans = () => unwrap<PassPlan[]>(api.get("/admin/passes/plans"))
export const createPass = (payload: PassIssuePayload) => unwrap<Pass>(api.post("/admin/passes", payload))
export const updatePass = (id: string, payload: PassUpdatePayload) => unwrap<Pass>(api.put("/admin/passes/" + id, payload))
export const deletePass = (id: string) => unwrap(api.delete("/admin/passes/" + id))
export const payPassInvoice = (passId: string, userId: string) =>
  unwrap<Pass>(api.post(`/client/pass/${passId}/pay`, null, { params: { user_id: userId } }))
export const fetchPassApplications = (status?: string) =>
  unwrap<PassApplication[]>(api.get("/admin/pass-applications", { params: status ? { status } : undefined }))
export const reviewPassApplication = (id: string, payload: PassApplicationDecisionPayload) =>
  unwrap<PassApplication>(api.post(`/admin/pass-applications/${id}/decision`, payload))

export const fetchAccessEvents = (limit = 50) => unwrap<AccessEvent[]>(api.get("/access-events", { params: { limit } }))
export const runInference = (payload: { gate: string; plate_override?: string; image_base64?: string }) =>
  unwrap<InferenceResponse>(api.post("/infer", payload))

export const fetchAnalytics = () => unwrap<AnalyticsResponse>(api.get("/analytics/mock"))

export const fetchGuestSessions = () => unwrap<GuestSession[]>(api.get("/guest/sessions"))
export const openGuestSession = (plate_text: string) => unwrap<GuestSession>(api.post("/guest/session/open", { plate_text }))
export const closeGuestSession = (session_id: string) => unwrap<GuestSession>(api.post("/guest/session/close", { session_id }))
export const payGuestSession = (session_id: string, amount?: number, paymentSource: "touchngo" | "wallet" = "touchngo") =>
  unwrap<Payment>(api.post("/guest/session/pay", { session_id, amount, payment_source: paymentSource }))
export const fetchGuestRate = () => unwrap<GuestRate>(api.get("/guest/rate"))
export const updateGuestRate = (payload: GuestRate) => unwrap<GuestRate>(api.put("/guest/rate", payload))

export const fetchGates = () => unwrap<GateConfig[]>(api.get("/admin/gates"))
export const createGate = (payload: Partial<GateConfig>) => unwrap<GateConfig>(api.post("/admin/gates", payload))
export const updateGate = (id: string, payload: Partial<GateConfig>) => unwrap<GateConfig>(api.put(`/admin/gates/${id}`, payload))
export const deleteGate = (id: string) => unwrap(api.delete(`/admin/gates/${id}`))

export const enrollFace = (payload: { user_id: string; image_base64: string }) =>
  unwrap<FaceEnrollResponse>(api.post("/face/enroll", payload))
export const verifyFace = (payload: { image_base64: string; top_k?: number; threshold?: number }) =>
  unwrap<FaceVerifyResponse>(api.post("/face/verify", payload))
export const fetchFaceProfiles = () => unwrap<UserFace[]>(api.get("/face/profiles"))

export const registerClient = (payload: ClientRegistrationRequest) =>
  unwrap<ClientRegistrationResponse>(api.post("/client/register", payload))
export const fetchClientSummary = (userId: string) => unwrap<ClientSummary>(api.get(`/client/summary/${userId}`))
export const fetchClientWallet = (userId: string) => unwrap<ClientWalletActivity>(api.get(`/client/wallet/${userId}`))
export const topUpClientWallet = (userId: string, payload: WalletTopUpRequest) =>
  unwrap<ClientWalletActivity>(api.post(`/client/wallet/${userId}/top-up`, payload))
export const submitClientRoleUpgrade = (userId: string, payload: RoleUpgradeSubmit) =>
  unwrap<RoleUpgradeRequest>(api.post(`/client/role-upgrade/${userId}`, payload))
export const lookupGuestSession = (params: { session_id?: string; plate_text?: string }) =>
  unwrap<GuestSessionLookupResponse>(api.get("/client/guest/lookup", { params }))
export const payGuestSessionClient = (payload: ClientGuestPaymentRequest) =>
  unwrap<Payment>(api.post("/client/guest/pay", payload))
export const fetchParkingOverview = () => unwrap<ParkingOverview>(api.get("/client/parking"))
export const fetchParkingVenues = () => unwrap<ParkingVenueStatus[]>(api.get("/parking/venues"))
export const recordParkingEvent = (payload: { venue_id: string; direction: "entry" | "exit" }) =>
  unwrap<ParkingVenueStatus>(api.post("/parking/event", payload))
export const createParkingVenue = (payload: ParkingVenuePayload) =>
  unwrap<ParkingVenueStatus>(api.post("/parking/venues", payload))
export const updateParkingVenue = (id: string, payload: ParkingVenuePayload) =>
  unwrap<ParkingVenueStatus>(api.put(`/parking/venues/${id}`, payload))
export const deleteParkingVenue = (id: string) => unwrap<APIMessage>(api.delete(`/parking/venues/${id}`))
export const fetchRoleUpgrades = (status?: string) =>
  unwrap<RoleUpgradeRequest[]>(api.get("/admin/role-upgrades", { params: status ? { status } : undefined }))
export const reviewRoleUpgrade = (requestId: string, payload: RoleUpgradeDecisionPayload) =>
  unwrap<RoleUpgradeRequest>(api.post(`/admin/role-upgrades/${requestId}/decision`, payload))
export const fetchNotifications = (userId: string) => unwrap<Notification[]>(api.get(`/client/notifications/${userId}`))
export const acknowledgeNotification = (userId: string, notificationId: string) =>
  unwrap<Notification>(api.post(`/client/notifications/${userId}/ack`, { notification_id: notificationId }))

export default api
