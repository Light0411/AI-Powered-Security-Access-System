from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, constr

RoleLiteral = Literal["guest", "student", "staff", "security", "admin"]
ClientStatusLiteral = Literal["pending", "active", "suspended"]
RoleUpgradeStatusLiteral = Literal["pending", "approved", "rejected"]
PassApplicationStatusLiteral = Literal["pending", "approved", "rejected"]
WalletTransactionTypeLiteral = Literal["top_up", "debit", "guest_payment", "refund", "pass_payment"]
DecisionLiteral = Literal["ALLOW", "DENY", "GUEST"]
GuestStatusLiteral = Literal["open", "closed", "paid"]
PassPlanLiteral = Literal["short_semester", "long_semester", "annual"]
ParkingDirectionLiteral = Literal["entry", "exit"]
SlugStr = constr(pattern=r"^[a-z0-9\-]+$")  # type: ignore[arg-type]


class APIMessage(BaseModel):
    message: str


class UserBase(BaseModel):
    name: str = Field(..., max_length=80)
    email: EmailStr
    phone: constr(min_length=7, max_length=20)  # type: ignore[arg-type]
    role: RoleLiteral = "student"
    programme: str = Field(..., max_length=80)


class UserCreate(UserBase):
    id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[RoleLiteral] = None
    programme: Optional[str] = None


class User(UserBase):
    id: str
    wallet_balance: Optional[float] = None


class VehicleBase(BaseModel):
    plate_text: constr(min_length=3, max_length=10)  # type: ignore[arg-type]
    user_id: str


class VehicleCreate(VehicleBase):
    id: Optional[str] = None


class VehicleUpdate(BaseModel):
    plate_text: Optional[str] = None
    user_id: Optional[str] = None


class Vehicle(VehicleBase):
    id: str


class PassPlan(BaseModel):
    plan_type: PassPlanLiteral
    label: str
    duration_days: int
    price_rm: float


class PassBase(BaseModel):
    user_id: str
    role: RoleLiteral
    plan_type: PassPlanLiteral
    valid_from: datetime
    valid_to: datetime
    price_rm: float
    is_paid: bool = False
    paid_at: Optional[datetime] = None


class PassCreate(BaseModel):
    id: Optional[str] = None
    user_id: str
    role: RoleLiteral
    plan_type: PassPlanLiteral
    starts_at: Optional[datetime] = None


class PassUpdate(BaseModel):
    role: Optional[RoleLiteral] = None
    plan_type: Optional[PassPlanLiteral] = None
    starts_at: Optional[datetime] = None


class Pass(PassBase):
    id: str


class PassApplication(BaseModel):
    id: str
    user_id: str
    role: RoleLiteral
    plan_type: PassPlanLiteral
    vehicles: List[str]
    status: PassApplicationStatusLiteral = "pending"
    review_note: Optional[str] = None
    reviewer_id: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None


class PassApplicationDecision(BaseModel):
    status: Literal["approved", "rejected"]
    reviewer_id: str
    note: Optional[str] = None


class AccessEventBase(BaseModel):
    plate_text: str
    confidence: float
    decision: DecisionLiteral
    gate: str = "outer"
    role: RoleLiteral
    reason: str
    snapshot_url: Optional[str] = None


class AccessEvent(AccessEventBase):
    id: str
    timestamp: datetime


class GuestSessionBase(BaseModel):
    plate_text: str
    start_time: datetime
    end_time: Optional[datetime] = None
    minutes: Optional[int] = None
    fee: Optional[float] = None
    status: GuestStatusLiteral = "open"


class GuestSessionCreate(BaseModel):
    plate_text: str


class GuestSessionClose(BaseModel):
    session_id: str


class GuestSession(GuestSessionBase):
    id: str


class Payment(BaseModel):
    id: str
    amount: float
    status: Literal["pending", "succeeded", "failed"]
    processor: str = "touchngo"
    timestamp: datetime
    currency: str = "MYR"
    session_id: Optional[str] = None
    pass_id: Optional[str] = None
    reference: Optional[str] = None


class GuestPaymentRequest(BaseModel):
    session_id: str
    amount: Optional[float] = None
    payment_source: Literal["touchngo", "wallet"] = "touchngo"


class ClientGuestPaymentRequest(GuestPaymentRequest):
    payment_source: Literal["touchngo", "wallet"] = "touchngo"
    user_id: Optional[str] = None


class AccessDecision(BaseModel):
    plate_text: str
    confidence: float
    decision: DecisionLiteral
    role: RoleLiteral
    reason: str
    gate: str
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_affiliation: Optional[str] = None
    pass_valid_to: Optional[datetime] = None


class InferenceRequest(BaseModel):
    gate: str = "outer"
    plate_override: Optional[str] = Field(
        default=None,
        description="Developer shortcut to bypass CV stack during demos.",
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Raw frame encoded as base64 string for YOLO/EasyOCR pipeline.",
    )


class InferenceResponse(BaseModel):
    decision: AccessDecision
    event: AccessEvent


class GateFrequencyPoint(BaseModel):
    timestamp: datetime
    outer: int
    inner: int


class GuestFeePoint(BaseModel):
    timestamp: datetime
    fee: float


class AnalyticsResponse(BaseModel):
    gate_frequency: List[GateFrequencyPoint]
    guest_fee_trend: List[GuestFeePoint]
    role_distribution: Dict[str, int]
    programme_distribution: Dict[str, int]
    guest_unpaid_ratio: float
    vehicle_distribution: Dict[str, int]


class GuestRateResponse(BaseModel):
    base_rate: float
    per_minute_rate: float


class GuestRateUpdate(BaseModel):
    base_rate: float
    per_minute_rate: float


class GateBase(BaseModel):
    name: str = Field(..., max_length=80)
    slug: SlugStr
    min_role: RoleLiteral = "guest"
    location: Optional[str] = Field(default=None, max_length=120)
    is_active: bool = True
    parking_venue_id: Optional[str] = Field(default=None, max_length=60)
    parking_direction: Optional[ParkingDirectionLiteral] = None


class GateCreate(GateBase):
    id: Optional[str] = None


class GateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=80)
    slug: Optional[SlugStr] = None
    min_role: Optional[RoleLiteral] = None
    location: Optional[str] = Field(default=None, max_length=120)
    is_active: Optional[bool] = None
    parking_venue_id: Optional[str] = Field(default=None, max_length=60)
    parking_direction: Optional[ParkingDirectionLiteral] = None


class Gate(GateBase):
    id: str


class UserFace(BaseModel):
    id: str
    user_id: str
    embedding: list[float]
    captured_at: datetime


class FaceEnrollRequest(BaseModel):
    user_id: str
    image_base64: str


class FaceEnrollResponse(BaseModel):
    message: str
    profile: UserFace


class FaceMatch(BaseModel):
    user_id: str
    score: float
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_affiliation: Optional[str] = None


class FaceVerifyRequest(BaseModel):
    image_base64: str
    top_k: int = Field(default=3, ge=1, le=5)
    threshold: float = Field(default=0.35, ge=0.0, le=1.0)


class FaceVerifyResponse(BaseModel):
    matches: List[FaceMatch]


class ClientRegistrationRequest(BaseModel):
    name: str = Field(..., max_length=80)
    email: EmailStr
    phone: constr(min_length=7, max_length=20)  # type: ignore[arg-type]
    programme: str = Field(..., max_length=80)
    role: RoleLiteral = "student"
    plan_type: PassPlanLiteral = "long_semester"
    vehicles: List[constr(min_length=3, max_length=10)] = Field(default_factory=list)  # type: ignore[arg-type]


class ClientRegistration(BaseModel):
    id: str
    user_id: str
    status: ClientStatusLiteral = "pending"
    submitted_at: datetime


class ClientProfile(BaseModel):
    user_id: str
    registration_id: str
    status: ClientStatusLiteral = "pending"
    guest_pin: str
    wallet_balance: float = 0.0
    created_at: datetime
    updated_at: datetime


class ClientRegistrationResponse(BaseModel):
    registration: ClientRegistration
    profile: ClientProfile
    user: User
    pass_info: Optional[Pass] = None
    vehicles: List[Vehicle]
    pass_application: PassApplication


class ClientWallet(BaseModel):
    user_id: str
    balance: float
    currency: str = "MYR"
    last_top_up: Optional[datetime] = None


class WalletTransaction(BaseModel):
    id: str
    user_id: str
    amount: float
    type: WalletTransactionTypeLiteral
    description: str
    timestamp: datetime
    source: str = "card"


class WalletTopUpRequest(BaseModel):
    amount: float = Field(..., gt=0.5)
    source: str = "card"


class ClientWalletActivity(BaseModel):
    wallet: ClientWallet
    transactions: List[WalletTransaction]


class RoleUpgradeSubmit(BaseModel):
    target_role: RoleLiteral
    reason: str = Field(..., max_length=280)
    attachments: List[str] = Field(default_factory=list)


class RoleUpgradeRequest(BaseModel):
    id: str
    user_id: str
    target_role: RoleLiteral
    reason: str
    attachments: List[str] = Field(default_factory=list)
    status: RoleUpgradeStatusLiteral = "pending"
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None


class RoleUpgradeDecision(BaseModel):
    status: RoleUpgradeStatusLiteral
    reviewer_id: str
    note: Optional[str] = None


class ClientSummary(BaseModel):
    user: User
    pass_info: Optional[Pass] = None
    vehicles: List[Vehicle]
    profile: ClientProfile
    wallet: ClientWallet
    guest_sessions: List[GuestSession]
    role_upgrades: List[RoleUpgradeRequest]
    pass_applications: List[PassApplication] = Field(default_factory=list)


class GuestSessionLookupResponse(BaseModel):
    session: GuestSession
    amount_due: float


class ParkingVenueStatus(BaseModel):
    id: str
    name: str
    capacity: int
    occupied: int
    percent: float


class ParkingOverview(BaseModel):
    venues: List[ParkingVenueStatus]


class ParkingVenueCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., max_length=120)
    capacity: int = Field(..., ge=0)
    occupied: int = Field(default=0, ge=0)


class ParkingVenueUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    capacity: Optional[int] = Field(default=None, ge=0)
    occupied: Optional[int] = Field(default=None, ge=0)


class ParkingEventRequest(BaseModel):
    venue_id: str
    direction: ParkingDirectionLiteral


class Notification(BaseModel):
    id: str
    user_id: str
    message: str
    created_at: datetime
    is_read: bool = False


class NotificationAck(BaseModel):
    notification_id: str


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: constr(min_length=7, max_length=20)  # type: ignore[arg-type]
    programme: str = Field(..., max_length=80)
    password: constr(min_length=6)  # type: ignore[arg-type]


class LoginRequest(BaseModel):
    identifier: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: User
