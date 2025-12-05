from __future__ import annotations

from datetime import datetime, timezone
from random import randint
from threading import RLock
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from loguru import logger

from app.core.config import settings
from app.core.passes import compute_validity_window, get_pass_plan
from app.data import seed
from app.schemas import (
    AccessEvent,
    AccessEventBase,
    AuthResponse,
    ClientGuestPaymentRequest,
    ClientProfile,
    ClientRegistration,
    ClientRegistrationRequest,
    ClientRegistrationResponse,
    ClientSummary,
    ClientWallet,
    ClientWalletActivity,
    Gate,
    GateCreate,
    GateUpdate,
    GuestPaymentRequest,
    GuestRateResponse,
    GuestRateUpdate,
    GuestSession,
    GuestSessionCreate,
    GuestSessionLookupResponse,
    LoginRequest,
    Notification,
    NotificationAck,
    ParkingEventRequest,
    ParkingOverview,
    ParkingVenueCreate,
    ParkingVenueStatus,
    ParkingVenueUpdate,
    Pass,
    PassCreate,
    PassUpdate,
    PassApplication,
    PassApplicationDecision,
    Payment,
    RoleUpgradeDecision,
    RoleUpgradeRequest,
    RoleUpgradeSubmit,
    SignupRequest,
    User,
    UserCreate,
    UserUpdate,
    Vehicle,
    VehicleCreate,
    VehicleUpdate,
    WalletTopUpRequest,
    WalletTransaction,
)

from .cache import CacheKeys, redis_cache
from .auth import auth_service
from .touchngo import touchngo_gateway


class MockDatabase:
    """Small in-memory store to keep the prototype self-contained."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.users: Dict[str, User] = {}
        self.vehicles: Dict[str, Vehicle] = {}
        self.passes: Dict[str, Pass] = {}
        self.access_events: List[AccessEvent] = []
        self.guest_sessions: Dict[str, GuestSession] = {}
        self.payments: Dict[str, Payment] = {}
        self.gates: Dict[str, Gate] = {}
        self.client_registrations: Dict[str, ClientRegistration] = {}
        self.client_profiles: Dict[str, ClientProfile] = {}
        self.wallet_transactions: Dict[str, List[WalletTransaction]] = {}
        self.role_upgrades: Dict[str, List[RoleUpgradeRequest]] = {}
        self.parking_venues: Dict[str, ParkingVenueStatus] = {}
        self.user_credentials: Dict[str, str] = {}
        self.notifications: Dict[str, List[Notification]] = {}
        self.pass_applications: Dict[str, PassApplication] = {}
        self.guest_rate: Dict[str, float] = {
            "base_rate": settings.base_guest_rate,
            "per_minute_rate": settings.per_minute_guest_rate,
        }
        self.seed()
        self._guest_cache_ttl = 4 * 60 * 60  # 4 hours, covers long visitor stays

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:6].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _normalize_plate(self, plate_text: str) -> str:
        cleaned = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in plate_text.upper())
        return " ".join(cleaned.split())

    def _create_pass_application(self, user_id: str, role: str, plan_type: str, vehicles: List[str]) -> PassApplication:
        app_id = self._generate_id("APP")
        normalized_vehicles: List[str] = []
        seen: set[str] = set()
        for plate in vehicles:
            normalized = self._normalize_plate(plate)
            if normalized and normalized not in seen:
                normalized_vehicles.append(normalized)
                seen.add(normalized)
        application = PassApplication(
            id=app_id,
            user_id=user_id,
            role=role,
            plan_type=plan_type,
            vehicles=normalized_vehicles,
            status="pending",
            submitted_at=self._now(),
        )
        self.pass_applications[app_id] = application
        self._create_notification(user_id, "Pass application submitted. Await admin review.")
        return application

    @staticmethod
    def _build_parking_venue(venue_id: str, name: str, capacity: int, occupied: int) -> ParkingVenueStatus:
        capacity = max(0, capacity)
        occupied = max(0, min(capacity, occupied))
        percent = round((occupied / capacity) * 100, 1) if capacity else 0.0
        return ParkingVenueStatus(id=venue_id, name=name, capacity=capacity, occupied=occupied, percent=percent)

    # ------------------------------------------------------------------
    # Seeds
    # ------------------------------------------------------------------
    def seed(self) -> None:
        with self._lock:
            logger.info("Seeding SmartGate demo data")
            self.users = {user.id: user for user in seed.seed_users()}
            self.vehicles = {vehicle.id: vehicle for vehicle in seed.seed_vehicles()}
            self.passes = {p.id: p for p in seed.seed_passes()}
            self.access_events = seed.seed_events()
            self.guest_sessions = {session.id: session for session in seed.seed_guest_sessions()}
            self.payments = {payment.id: payment for payment in seed.seed_payments()}
            self.gates = {gate.id: gate for gate in seed.seed_gates()}
            self.parking_venues = {venue.id: venue for venue in seed.seed_parking_venues()}
            self.client_registrations.clear()
            self.client_profiles.clear()
            self.wallet_transactions.clear()
            self.role_upgrades.clear()
            self.user_credentials.clear()
            self.pass_applications.clear()
            self._seed_client_profiles()
            self._seed_credentials()

    def _seed_client_profiles(self) -> None:
        now = self._now()
        for idx, user in enumerate(self.users.values(), start=1):
            registration_id = self._generate_id("REG")
            status = "active" if user.role != "guest" else "pending"
            balance = 35.0 - 5 * idx if status == "active" else 10.0
            registration = ClientRegistration(
                id=registration_id,
                user_id=user.id,
                status=status,
                submitted_at=now,
            )
            profile = ClientProfile(
                user_id=user.id,
                registration_id=registration_id,
                status=status,
                guest_pin=f"{randint(1000, 9999)}",
                wallet_balance=round(balance, 2),
                created_at=now,
                updated_at=now,
            )
            self.client_registrations[registration_id] = registration
            self.client_profiles[user.id] = profile
            txn = WalletTransaction(
                id=self._generate_id("TXN"),
                user_id=user.id,
                amount=profile.wallet_balance,
                type="top_up",
                description="Seed credit",
                timestamp=now,
                source="seed",
            )
            self.wallet_transactions[user.id] = [txn]
            self.notifications[user.id] = []

    def _seed_credentials(self) -> None:
        default_password = "password"
        hashed = auth_service.hash_password(default_password)
        for user in self.users.values():
            self.user_credentials[user.id] = hashed


    # ------------------------------------------------------------------
    # Users CRUD
    # ------------------------------------------------------------------
    def list_users(self) -> List[User]:
        enriched: List[User] = []
        for user in self.users.values():
            profile = self._ensure_client_profile(user.id)
            enriched.append(user.model_copy(update={"wallet_balance": round(profile.wallet_balance, 2)}))
        return enriched

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def create_user(self, payload: UserCreate) -> User:
        with self._lock:
            user_id = payload.id or self._generate_id("USR")
            user = User(id=user_id, **payload.model_dump(exclude={"id"}))
            self.users[user.id] = user
            self.user_credentials[user.id] = auth_service.hash_password("password")
            return user

    def update_user(self, user_id: str, payload: UserUpdate) -> User:
        with self._lock:
            if user_id not in self.users:
                raise KeyError(user_id)
            user = self.users[user_id]
            updated = user.model_copy(update=payload.model_dump(exclude_unset=True))
            self.users[user_id] = updated
            return updated

    def delete_user(self, user_id: str) -> None:
        with self._lock:
            if user_id not in self.users:
                raise KeyError(user_id)
            self.users.pop(user_id)
            vehicles_to_remove = [vid for vid, vehicle in self.vehicles.items() if vehicle.user_id == user_id]
            for vid in vehicles_to_remove:
                self.vehicles.pop(vid, None)
            passes_to_remove = [pid for pid, parking_pass in self.passes.items() if parking_pass.user_id == user_id]
            for pid in passes_to_remove:
                self.passes.pop(pid, None)

    # ------------------------------------------------------------------
    # Vehicles CRUD
    # ------------------------------------------------------------------
    def list_vehicles(self) -> List[Vehicle]:
        return list(self.vehicles.values())

    def create_vehicle(self, payload: VehicleCreate) -> Vehicle:
        with self._lock:
            if payload.user_id not in self.users:
                raise KeyError(payload.user_id)
            vehicle_id = payload.id or self._generate_id("VEH")
            vehicle = Vehicle(id=vehicle_id, **payload.model_dump(exclude={"id"}))
            self.vehicles[vehicle.id] = vehicle
            return vehicle

    def update_vehicle(self, vehicle_id: str, payload: VehicleUpdate) -> Vehicle:
        with self._lock:
            if vehicle_id not in self.vehicles:
                raise KeyError(vehicle_id)
            current = self.vehicles[vehicle_id]
            if payload.user_id and payload.user_id not in self.users:
                raise KeyError(payload.user_id)
            updated = current.model_copy(update=payload.model_dump(exclude_unset=True))
            self.vehicles[vehicle_id] = updated
            return updated

    def delete_vehicle(self, vehicle_id: str) -> None:
        with self._lock:
            if vehicle_id not in self.vehicles:
                raise KeyError(vehicle_id)
            self.vehicles.pop(vehicle_id)

    # ------------------------------------------------------------------
    # Passes CRUD
    # ------------------------------------------------------------------
    def list_passes(self) -> List[Pass]:
        return list(self.passes.values())

    def create_pass(self, payload: PassCreate) -> Pass:
        with self._lock:
            self._require_user(payload.user_id)
            starts_at = payload.starts_at or self._now()
            valid_from, valid_to, plan = compute_validity_window(payload.plan_type, starts_at=starts_at)
            pass_id = payload.id or self._generate_id("PASS")
            parking_pass = Pass(
                id=pass_id,
                user_id=payload.user_id,
                role=payload.role,
                plan_type=plan.plan_type,
                valid_from=valid_from,
                valid_to=valid_to,
                price_rm=plan.price_rm,
                is_paid=False,
                paid_at=None,
            )
            self.passes[pass_id] = parking_pass
            self._create_notification(
                payload.user_id,
                f"{plan.label} pass issued. Pay RM {plan.price_rm:.2f} via wallet.",
            )
            return parking_pass

    def update_pass(self, pass_id: str, payload: PassUpdate) -> Pass:
        with self._lock:
            if pass_id not in self.passes:
                raise KeyError(pass_id)
            current = self.passes[pass_id]
            fields = payload.model_dump(exclude_unset=True)
            plan_type = fields.pop("plan_type", None)
            starts_at = fields.pop("starts_at", None)
            if plan_type or starts_at:
                target_plan = plan_type or current.plan_type
                base_start = starts_at or current.valid_from
                valid_from, valid_to, plan = compute_validity_window(target_plan, starts_at=base_start)
                fields.update(
                    {
                        "plan_type": plan.plan_type,
                        "valid_from": valid_from,
                        "valid_to": valid_to,
                        "price_rm": plan.price_rm,
                        "is_paid": False,
                        "paid_at": None,
                    }
                )
                self._create_notification(
                    current.user_id,
                    f"{plan.label} pass updated. Pay RM {plan.price_rm:.2f} via wallet.",
                )
            updated = current.model_copy(update=fields)
            self.passes[pass_id] = updated
            return updated

    def delete_pass(self, pass_id: str) -> None:
        with self._lock:
            if pass_id not in self.passes:
                raise KeyError(pass_id)
            self.passes.pop(pass_id)

    def get_latest_pass(self, user_id: str) -> Optional[Pass]:
        passes = [parking_pass for parking_pass in self.passes.values() if parking_pass.user_id == user_id]
        if not passes:
            return None
        return max(passes, key=lambda p: p.valid_to)

    def list_pass_applications(self, status: Optional[str] = None) -> List[PassApplication]:
        apps = list(self.pass_applications.values())
        if status:
            apps = [app for app in apps if app.status == status]
        return sorted(apps, key=lambda app: app.submitted_at, reverse=True)

    def review_pass_application(self, app_id: str, payload: PassApplicationDecision) -> PassApplication:
        with self._lock:
            application = self.pass_applications.get(app_id)
            if not application:
                raise KeyError(app_id)
            if application.status != "pending":
                return application
            now = self._now()
            updated = application.model_copy(
                update={
                    "status": payload.status,
                    "reviewer_id": payload.reviewer_id,
                    "review_note": payload.note,
                    "reviewed_at": now,
                }
            )
            self.pass_applications[app_id] = updated
            if payload.status == "approved":
                self.create_pass(
                    PassCreate(
                        user_id=application.user_id,
                        role=application.role,
                        plan_type=application.plan_type,
                        starts_at=now,
                    )
                )
            else:
                self._create_notification(application.user_id, payload.note or "Pass application rejected")
            return updated

    # ------------------------------------------------------------------
    # Access events
    # ------------------------------------------------------------------
    def list_access_events(self, limit: int = 50) -> List[AccessEvent]:
        cached = redis_cache.list_json(CacheKeys.access_events(), limit)
        if cached:
            return [AccessEvent(**entry) for entry in cached]
        return self.access_events[:limit]

    def add_access_event(self, payload: AccessEventBase) -> AccessEvent:
        with self._lock:
            event = AccessEvent(
                id=self._generate_id("EVT"),
                timestamp=self._now(),
                **payload.model_dump(),
            )
            self.access_events.insert(0, event)
            self.access_events = self.access_events[:200]
            return event

    def find_user_by_plate(self, plate_text: str) -> Tuple[Optional[User], Optional[Vehicle]]:
        normalized = self._normalize_plate(plate_text)
        for vehicle in self.vehicles.values():
            if self._normalize_plate(vehicle.plate_text) == normalized:
                return self.users.get(vehicle.user_id), vehicle
        return None, None

    # ------------------------------------------------------------------
    # Gates
    # ------------------------------------------------------------------
    def list_gates(self) -> List[Gate]:
        return list(self.gates.values())

    def create_gate(self, payload: GateCreate) -> Gate:
        with self._lock:
            slug = payload.slug.lower()
            if any(gate.slug == slug for gate in self.gates.values()):
                raise ValueError(f"Gate slug {slug} already exists")
            gate_id = payload.id or self._generate_id("GTE")
            gate = Gate(
                id=gate_id,
                name=payload.name,
                slug=slug,
                min_role=payload.min_role,
                location=payload.location,
                is_active=payload.is_active,
                parking_venue_id=payload.parking_venue_id,
                parking_direction=payload.parking_direction,
            )
            self.gates[gate.id] = gate
            return gate

    def update_gate(self, gate_id: str, payload: GateUpdate) -> Gate:
        with self._lock:
            if gate_id not in self.gates:
                raise KeyError(gate_id)
            current = self.gates[gate_id]
            updated_slug = payload.slug.lower() if payload.slug else current.slug
            if updated_slug != current.slug and any(g.slug == updated_slug for g in self.gates.values()):
                raise ValueError(f"Gate slug {updated_slug} already exists")
            updated = current.model_copy(
                update={
                    **payload.model_dump(exclude_unset=True),
                    "slug": updated_slug,
                }
            )
            self.gates[gate_id] = updated
            return updated

    def delete_gate(self, gate_id: str) -> None:
        with self._lock:
            if gate_id not in self.gates:
                raise KeyError(gate_id)
            self.gates.pop(gate_id)

    def get_gate(self, gate_id: str) -> Optional[Gate]:
        return self.gates.get(gate_id)

    def get_gate_by_slug(self, slug: str) -> Optional[Gate]:
        target = slug.lower()
        for gate in self.gates.values():
            if gate.slug == target:
                return gate
        return None

    # ------------------------------------------------------------------
    # Guest sessions
    # ------------------------------------------------------------------
    def list_guest_sessions(self) -> List[GuestSession]:
        return list(self.guest_sessions.values())

    def find_guest_session_by_plate(self, plate_text: str, status: Optional[str] = None) -> Optional[GuestSession]:
        normalized = plate_text.upper()
        cached = redis_cache.get_json(CacheKeys.guest_session(normalized))
        if cached:
            session = GuestSession(**cached)
            if status is None or session.status == status:
                return session
        for session in self.guest_sessions.values():
            if session.plate_text.upper() == normalized and (status is None or session.status == status):
                self._cache_guest_session(session)
                return session
        return None

    def open_guest_session(self, payload: GuestSessionCreate) -> GuestSession:
        with self._lock:
            session_id = self._generate_id("GST")
            session = GuestSession(
                id=session_id,
                plate_text=payload.plate_text.upper(),
                start_time=self._now(),
                status="open",
            )
            self.guest_sessions[session.id] = session
            self._cache_guest_session(session)
            return session

    def close_guest_session(self, session_id: str) -> GuestSession:
        with self._lock:
            session = self._require_guest_session(session_id)
            if session.status == "open":
                end_time = self._now()
                minutes = max(1, int((end_time - session.start_time).total_seconds() // 60))
                fee = self.compute_guest_fee(minutes)
                session = session.model_copy(update={
                    "end_time": end_time,
                    "minutes": minutes,
                    "fee": round(fee, 2),
                    "status": "closed",
                })
                self.guest_sessions[session_id] = session
                self._cache_guest_session(session)
            return session

    def pay_guest_session(self, payload: GuestPaymentRequest) -> Payment:
        with self._lock:
            session = self._require_guest_session(payload.session_id)
            minutes = session.minutes or max(1, int((self._now() - session.start_time).total_seconds() // 60))
            fee = payload.amount or session.fee or self.compute_guest_fee(minutes)
            session = session.model_copy(
                update={
                    "end_time": session.end_time or self._now(),
                    "minutes": session.minutes or minutes,
                    "fee": round(fee, 2),
                    "status": "paid",
                }
            )
            self.guest_sessions[session.id] = session
            charge = None
            processor = "wallet" if payload.payment_source == "wallet" else "touchngo"
            reference = None
            if payload.payment_source != "wallet":
                charge = touchngo_gateway.charge_guest(
                    session_id=session.id,
                    amount_rm=fee,
                    plate_text=session.plate_text,
                )
                processor = charge.processor
                reference = charge.transaction_id
            payment = self._record_payment(
                amount=fee,
                processor=processor,
                reference=reference,
                session_id=session.id,
            )
            self._cache_guest_session(session)
            return payment

    def list_payments(self) -> List[Payment]:
        return list(self.payments.values())

    def get_guest_rate(self) -> GuestRateResponse:
        return GuestRateResponse(**self.guest_rate)

    def update_guest_rate(self, payload: GuestRateUpdate) -> GuestRateResponse:
        with self._lock:
            self.guest_rate.update(payload.model_dump())
            return self.get_guest_rate()

    def compute_guest_fee(self, minutes: int) -> float:
        base = self.guest_rate["base_rate"]
        per_minute = self.guest_rate["per_minute_rate"]
        return base + per_minute * max(0, minutes)

    # ------------------------------------------------------------------
    # Client portal / mobile flows
    # ------------------------------------------------------------------
    def register_client(self, payload: ClientRegistrationRequest) -> ClientRegistrationResponse:
        if payload.role == "guest":
            raise ValueError("Guest role cannot receive parking passes")
        with self._lock:
            existing = self._find_user_by_email(payload.email)
            if existing:
                user = existing
                if payload.role != "guest" and existing.role != payload.role:
                    user = existing.model_copy(update={"role": payload.role})
                    self.users[user.id] = user
            else:
                user = User(
                    id=self._generate_id("USR"),
                    name=payload.name,
                    email=payload.email,
                    phone=payload.phone,
                    role=payload.role,
                    programme=payload.programme,
                )
                self.users[user.id] = user
            registration = self._ensure_client_registration(user.id, status="pending")
            profile = self._ensure_client_profile(user.id, default_status="pending")
            profile = profile.model_copy(update={"status": "pending", "updated_at": self._now()})
            self.client_profiles[user.id] = profile
            parking_pass = next((p for p in self.passes.values() if p.user_id == user.id), None)
            application = self._create_pass_application(user.id, payload.role, payload.plan_type, payload.vehicles)
            existing_plates: set[str] = set()
            for vehicle in self.vehicles.values():
                normalized_plate = self._normalize_plate(vehicle.plate_text)
                if normalized_plate:
                    existing_plates.add(normalized_plate)
            for plate in payload.vehicles:
                normalized = self._normalize_plate(plate)
                if not normalized or normalized in existing_plates:
                    continue
                vehicle = Vehicle(
                    id=self._generate_id("VEH"),
                    plate_text=normalized,
                    user_id=user.id,
                )
                self.vehicles[vehicle.id] = vehicle
                existing_plates.add(normalized)
            vehicles = [vehicle for vehicle in self.vehicles.values() if vehicle.user_id == user.id]
            registration = registration.model_copy(update={"status": "pending"})
            self.client_registrations[registration.id] = registration
        return ClientRegistrationResponse(
            registration=registration,
            profile=profile,
            user=user,
            pass_info=parking_pass,
            vehicles=vehicles,
            pass_application=application,
        )

    def signup_portal_user(self, payload: SignupRequest) -> AuthResponse:
        with self._lock:
            if self._find_user_by_email(payload.email):
                raise ValueError("Email already registered")
            user = User(
                id=self._generate_id("USR"),
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                role="guest",
                programme=payload.programme,
            )
            self.users[user.id] = user
            self.user_credentials[user.id] = auth_service.hash_password(payload.password)
            self._ensure_client_profile(user.id, default_status="pending")
            token = auth_service.create_token({"user_id": user.id})
            return AuthResponse(token=token, user=user)

    def login_portal_user(self, payload: LoginRequest) -> AuthResponse:
        identifier = payload.identifier.lower()
        target: Optional[User] = None
        for user in self.users.values():
            if user.email.lower() == identifier or user.name.lower() == identifier or user.id.lower() == identifier:
                target = user
                break
        if not target:
            raise ValueError("User not found")
        hashed = self.user_credentials.get(target.id)
        if not hashed or not auth_service.verify_password(payload.password, hashed):
            raise ValueError("Invalid credentials")
        token = auth_service.create_token({"user_id": target.id})
        return AuthResponse(token=token, user=target)

    def get_client_summary(self, user_id: str) -> ClientSummary:
        with self._lock:
            user = self._require_user(user_id)
            pass_info = next((p for p in self.passes.values() if p.user_id == user_id), None)
            vehicles = [vehicle for vehicle in self.vehicles.values() if vehicle.user_id == user_id]
            profile = self._ensure_client_profile(
                user_id,
                default_status="active" if user.role != "guest" else "pending",
            )
            wallet = self._wallet_snapshot(user_id)
            guest_sessions = self._guest_sessions_for_user(vehicles)
            upgrades = list(self.role_upgrades.get(user_id, []))
            applications = sorted(
                (app for app in self.pass_applications.values() if app.user_id == user_id),
                key=lambda app: app.submitted_at,
                reverse=True,
            )
            return ClientSummary(
                user=user,
                pass_info=pass_info,
                vehicles=vehicles,
                profile=profile,
                wallet=wallet,
                guest_sessions=guest_sessions,
                role_upgrades=upgrades,
                pass_applications=applications,
            )

    def wallet_top_up(self, user_id: str, payload: WalletTopUpRequest) -> ClientWalletActivity:
        with self._lock:
            self._require_user(user_id)
            charge = touchngo_gateway.charge_wallet_top_up(user_id=user_id, amount_rm=payload.amount)
            txn = self._apply_wallet_delta(
                user_id,
                delta=payload.amount,
                txn_type="top_up",
                description=f"Wallet top-up ({payload.source})",
                source=payload.source,
            )
            self._record_payment(
                amount=payload.amount,
                processor=charge.processor,
                reference=charge.transaction_id,
                session_id=None,
                pass_id=None,
            )
            return self._wallet_activity(user_id)

    def get_wallet_activity(self, user_id: str) -> ClientWalletActivity:
        with self._lock:
            self._require_user(user_id)
            return self._wallet_activity(user_id)

    def submit_role_upgrade(self, user_id: str, payload: RoleUpgradeSubmit) -> RoleUpgradeRequest:
        with self._lock:
            self._require_user(user_id)
            request = RoleUpgradeRequest(
                id=self._generate_id("URQ"),
                user_id=user_id,
                target_role=payload.target_role,
                reason=payload.reason,
                attachments=payload.attachments,
                status="pending",
                submitted_at=self._now(),
                reviewed_at=None,
            )
            self.role_upgrades.setdefault(user_id, []).insert(0, request)
            profile = self._ensure_client_profile(user_id)
            self.client_profiles[user_id] = profile.model_copy(update={"status": "pending", "updated_at": self._now()})
            return request

    def list_role_upgrades(self, status: Optional[str] = None) -> List[RoleUpgradeRequest]:
        with self._lock:
            requests = [req for bucket in self.role_upgrades.values() for req in bucket]
            if status:
                requests = [req for req in requests if req.status == status]
            return sorted(requests, key=lambda req: req.submitted_at, reverse=True)

    def review_role_upgrade(self, request_id: str, payload: RoleUpgradeDecision) -> RoleUpgradeRequest:
        with self._lock:
            target: Optional[RoleUpgradeRequest] = None
            owner_id: Optional[str] = None
            for user_id, requests in self.role_upgrades.items():
                for idx, req in enumerate(requests):
                    if req.id == request_id:
                        target = req
                        owner_id = user_id
                        break
                if target:
                    break
            if not target or not owner_id:
                raise KeyError(request_id)
            now = self._now()
            target = target.model_copy(
                update={
                    "status": payload.status,
                    "reviewed_at": now,
                    "reviewer_id": payload.reviewer_id,
                }
            )
            requests = self.role_upgrades[owner_id]
            self.role_upgrades[owner_id] = [target if req.id == request_id else req for req in requests]
            if payload.status == "approved":
                user = self.users.get(owner_id)
                if user:
                    upgraded = user.model_copy(update={"role": target.target_role})
                    self.users[owner_id] = upgraded
                for idx, existing in enumerate(self.passes.values()):
                    if existing.user_id == owner_id:
                        self.passes[existing.id] = existing.model_copy(update={"role": target.target_role})
                        break
            message = (
                f"Role upgrade request {target.target_role} {payload.status.upper()}"
                if not payload.note
                else f"{payload.note}"
            )
            self._create_notification(owner_id, message)
            return target

    def get_parking_overview(self) -> ParkingOverview:
        with self._lock:
            venues: List[ParkingVenueStatus] = []
            for venue in self.parking_venues.values():
                percent = round((venue.occupied / venue.capacity) * 100, 1) if venue.capacity else 0.0
                venues.append(venue.model_copy(update={"percent": percent}))
            return ParkingOverview(venues=venues)

    def list_parking_venues(self) -> List[ParkingVenueStatus]:
        return list(self.parking_venues.values())

    def create_parking_venue(self, payload: ParkingVenueCreate) -> ParkingVenueStatus:
        with self._lock:
            venue_id = payload.id or self._generate_id("VEN")
            if venue_id in self.parking_venues:
                raise ValueError(f"Venue {venue_id} already exists")
            venue = self._build_parking_venue(venue_id, payload.name, payload.capacity, payload.occupied)
            self.parking_venues[venue_id] = venue
            return venue

    def update_parking_venue(self, venue_id: str, payload: ParkingVenueUpdate) -> ParkingVenueStatus:
        with self._lock:
            venue = self.parking_venues.get(venue_id)
            if not venue:
                raise KeyError(venue_id)
            name = payload.name if payload.name is not None else venue.name
            capacity = payload.capacity if payload.capacity is not None else venue.capacity
            occupied = payload.occupied if payload.occupied is not None else venue.occupied
            updated = self._build_parking_venue(venue_id, name, capacity, occupied)
            self.parking_venues[venue_id] = updated
            return updated

    def delete_parking_venue(self, venue_id: str) -> None:
        with self._lock:
            if venue_id not in self.parking_venues:
                raise KeyError(venue_id)
            self.parking_venues.pop(venue_id, None)
            for gate_id, gate in list(self.gates.items()):
                if gate.parking_venue_id == venue_id:
                    self.gates[gate_id] = gate.model_copy(update={"parking_venue_id": None, "parking_direction": None})

    def record_parking_event(self, payload: ParkingEventRequest) -> ParkingVenueStatus:
        with self._lock:
            venue = self.parking_venues.get(payload.venue_id)
            if not venue:
                raise KeyError(payload.venue_id)
            delta = 1 if payload.direction == "entry" else -1
            occupied = max(0, min(venue.capacity, venue.occupied + delta))
            percent = round((occupied / venue.capacity) * 100, 1) if venue.capacity else 0.0
            updated = venue.model_copy(update={"occupied": occupied, "percent": percent})
            self.parking_venues[venue.id] = updated
            return updated

    def lookup_guest_session(self, session_id: Optional[str] = None, plate_text: Optional[str] = None) -> GuestSessionLookupResponse:
        if not session_id and not plate_text:
            raise KeyError("guest_session_lookup_requires_identifier")
        with self._lock:
            return self._resolve_guest_session(session_id=session_id, plate_text=plate_text)

    def client_pay_guest_session(self, payload: ClientGuestPaymentRequest) -> Payment:
        if not payload.session_id:
            raise ValueError("session_id required")
        amount_to_pay: Optional[float] = None
        if payload.payment_source == "wallet" and not payload.user_id:
            raise ValueError("user_id required for wallet payments")
        with self._lock:
            lookup = self._resolve_guest_session(session_id=payload.session_id, plate_text=None)
            amount_to_pay = round(payload.amount or lookup.amount_due, 2)
            if payload.payment_source == "wallet" and payload.user_id:
                self._apply_wallet_delta(
                    payload.user_id,
                    delta=-amount_to_pay,
                    txn_type="guest_payment",
                    description=f"Guest session {payload.session_id}",
                    source="wallet",
                )
        return self.pay_guest_session(
            GuestPaymentRequest(
                session_id=payload.session_id,
                amount=amount_to_pay,
                payment_source=payload.payment_source,
            )
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _require_guest_session(self, session_id: str) -> GuestSession:
        if session_id not in self.guest_sessions:
            raise KeyError(session_id)
        return self.guest_sessions[session_id]

    def _cache_guest_session(self, session: GuestSession) -> None:
        ttl = self._guest_cache_ttl
        key = CacheKeys.guest_session(session.plate_text)
        if session.status == "open":
            redis_cache.set_json(key, session.model_dump(mode="json"), ttl=ttl)
        else:
            redis_cache.delete(key)

    def _require_user(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if not user:
            raise KeyError(user_id)
        return user

    def _find_user_by_email(self, email: str) -> Optional[User]:
        target = email.lower()
        for user in self.users.values():
            if user.email.lower() == target:
                return user
        return None

    def _ensure_client_registration(self, user_id: str, status: str = "pending") -> ClientRegistration:
        for registration in self.client_registrations.values():
            if registration.user_id == user_id:
                return registration
        registration = ClientRegistration(
            id=self._generate_id("REG"),
            user_id=user_id,
            status=status,
            submitted_at=self._now(),
        )
        self.client_registrations[registration.id] = registration
        return registration

    def _ensure_client_profile(self, user_id: str, default_status: str = "pending") -> ClientProfile:
        profile = self.client_profiles.get(user_id)
        if profile:
            return profile
        registration = self._ensure_client_registration(user_id, status=default_status)
        now = self._now()
        profile = ClientProfile(
            user_id=user_id,
            registration_id=registration.id,
            status=default_status,
            guest_pin=f"{randint(1000, 9999)}",
            wallet_balance=0.0,
            created_at=now,
            updated_at=now,
        )
        self.client_profiles[user_id] = profile
        self.wallet_transactions.setdefault(user_id, [])
        return profile

    def _wallet_snapshot(self, user_id: str) -> ClientWallet:
        profile = self.client_profiles.get(user_id) or self._ensure_client_profile(user_id)
        transactions = self.wallet_transactions.get(user_id, [])
        last_top_up = next((txn.timestamp for txn in transactions if txn.type == "top_up"), None) if transactions else None
        return ClientWallet(
            user_id=user_id,
            balance=round(profile.wallet_balance, 2),
            last_top_up=last_top_up,
            currency=settings.currency_code,
        )

    def _wallet_activity(self, user_id: str) -> ClientWalletActivity:
        wallet = self._wallet_snapshot(user_id)
        transactions = list(self.wallet_transactions.get(user_id, []))[:20]
        return ClientWalletActivity(wallet=wallet, transactions=transactions)

    def _record_payment(
        self,
        *,
        amount: float,
        processor: str,
        reference: Optional[str],
        session_id: Optional[str] = None,
        pass_id: Optional[str] = None,
    ) -> Payment:
        payment = Payment(
            id=self._generate_id("PAY"),
            amount=round(amount, 2),
            status="succeeded",
            processor=processor,
            timestamp=self._now(),
            currency=settings.currency_code,
            session_id=session_id,
            pass_id=pass_id,
            reference=reference,
        )
        self.payments[payment.id] = payment
        return payment

    def _apply_wallet_delta(
        self,
        user_id: str,
        *,
        delta: float,
        txn_type: str,
        description: str,
        source: str,
    ) -> WalletTransaction:
        profile = self._ensure_client_profile(user_id)
        new_balance = round(profile.wallet_balance + delta, 2)
        if new_balance < -1e-6:
            raise ValueError("Insufficient wallet balance")
        profile = profile.model_copy(update={"wallet_balance": new_balance, "updated_at": self._now()})
        self.client_profiles[user_id] = profile
        transaction = WalletTransaction(
            id=self._generate_id("TXN"),
            user_id=user_id,
            amount=round(delta, 2),
            type=txn_type,  # type: ignore[arg-type]
            description=description,
            timestamp=self._now(),
            source=source,
        )
        self.wallet_transactions.setdefault(user_id, []).insert(0, transaction)
        return transaction

    def pay_pass_invoice(self, user_id: str, pass_id: str) -> Pass:
        with self._lock:
            if pass_id not in self.passes:
                raise KeyError(pass_id)
            parking_pass = self.passes[pass_id]
            if parking_pass.user_id != user_id:
                raise ValueError("Pass does not belong to user")
            if parking_pass.is_paid:
                return parking_pass
            price = parking_pass.price_rm
            txn = self._apply_wallet_delta(
                user_id,
                delta=-price,
                txn_type="pass_payment",
                description=f"Pass {parking_pass.plan_type}",
                source="wallet",
            )
            paid_pass = parking_pass.model_copy(update={"is_paid": True, "paid_at": self._now()})
            self.passes[pass_id] = paid_pass
            self._record_payment(
                amount=price,
                processor="wallet",
                reference=txn.id,
                pass_id=pass_id,
            )
            self._create_notification(user_id, f"Pass payment received: RM {price:.2f}")
            return paid_pass

    def _guest_sessions_for_user(self, vehicles: List[Vehicle]) -> List[GuestSession]:
        plates = {vehicle.plate_text.upper() for vehicle in vehicles}
        if not plates:
            return []
        sessions: List[GuestSession] = []
        for session in self.guest_sessions.values():
            if session.plate_text.upper() in plates:
                sessions.append(session)
        return sorted(sessions, key=lambda s: s.start_time, reverse=True)

    def _resolve_guest_session(self, session_id: Optional[str], plate_text: Optional[str]) -> GuestSessionLookupResponse:
        session: Optional[GuestSession] = None
        if session_id:
            session = self.guest_sessions.get(session_id)
        if not session and plate_text:
            session = self.find_guest_session_by_plate(plate_text, status=None)
        if not session:
            identifier = session_id or plate_text or "session"
            raise KeyError(identifier)
        minutes = session.minutes or max(1, int((self._now() - session.start_time).total_seconds() // 60))
        fee = session.fee or self.compute_guest_fee(minutes)
        return GuestSessionLookupResponse(session=session, amount_due=round(fee, 2))

    def list_notifications(self, user_id: str) -> List[Notification]:
        notes = self.notifications.get(user_id, [])
        return sorted(notes, key=lambda note: note.created_at, reverse=True)

    def acknowledge_notification(self, user_id: str, notification_id: str) -> Notification:
        notes = self.notifications.get(user_id, [])
        for idx, note in enumerate(notes):
            if note.id == notification_id:
                updated = note.model_copy(update={"is_read": True})
                notes[idx] = updated
                return updated
        raise KeyError(notification_id)

    def _create_notification(self, user_id: str, message: str) -> Notification:
        note = Notification(
            id=self._generate_id("NTF"),
            user_id=user_id,
            message=message,
            created_at=self._now(),
            is_read=False,
        )
        self.notifications.setdefault(user_id, []).insert(0, note)
        return note


if settings.use_supabase:
    from .supabase_store import SupabaseStore

    db = SupabaseStore()
else:
    db = MockDatabase()
