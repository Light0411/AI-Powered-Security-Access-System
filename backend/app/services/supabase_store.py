from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from random import randint
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from loguru import logger
from supabase import Client, create_client

from app.core.config import settings
from app.core.passes import compute_validity_window
from app.core.passes import compute_validity_window
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
    ParkingEventRequest,
    ParkingOverview,
    ParkingVenueCreate,
    ParkingVenueStatus,
    ParkingVenueUpdate,
    Pass,
    PassApplication,
    PassApplicationDecision,
    PassCreate,
    PassUpdate,
    Payment,
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

from .auth import auth_service
from .cache import CacheKeys, redis_cache
from .touchngo import touchngo_gateway


class SupabaseStore:
    """Supabase-backed data layer mirroring the MockDatabase API."""

    RATE_SINGLETON_ID = "default"

    def __init__(self) -> None:
        self.client: Client = create_client(settings.supabase_url, settings.supabase_key)
        self._guest_rate_cache: Dict[str, float] = {
            "base_rate": settings.base_guest_rate,
            "per_minute_rate": settings.per_minute_guest_rate,
        }
        self._client_registrations: Dict[str, ClientRegistration] = {}
        self._client_profiles: Dict[str, ClientProfile] = {}
        self._wallet_transactions: Dict[str, List[WalletTransaction]] = {}
        self._role_upgrades: Dict[str, List[RoleUpgradeRequest]] = {}
        self._parking_venues: Dict[str, ParkingVenueStatus] = {venue.id: venue for venue in seed.seed_parking_venues()}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:6].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_plate(plate_text: str) -> str:
        cleaned = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in plate_text.upper())
        return " ".join(cleaned.split())

    def _execute(self, query) -> List[Dict]:
        response = query.execute()
        if getattr(response, "error", None):
            raise RuntimeError(response.error.message)  # pragma: no cover - depends on Supabase
        return response.data or []

    def _insert_row(self, table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.table(table).insert(payload).execute()
        if getattr(response, "error", None):
            raise RuntimeError(response.error.message)
        if not response.data:
            raise RuntimeError(f"Supabase insert into {table} returned no data")
        return response.data[0]

    def _single(self, query) -> Optional[Dict]:
        data = self._execute(query.limit(1))
        return data[0] if data else None

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def list_users(self) -> List[User]:
        data = self._execute(self.client.table("users").select("*").order("name"))
        return [User(**row) for row in data]

    def get_user(self, user_id: str) -> Optional[User]:
        row = self._single(self.client.table("users").select("*").eq("id", user_id))
        return User(**row) if row else None

    def create_user(self, payload: UserCreate) -> User:
        body = payload.model_dump(exclude={"id"})
        body["id"] = payload.id or self._generate_id("USR")
        body["wallet_balance"] = body.get("wallet_balance") or 0
        row = self._insert_row("users", body)
        self._insert_row(
            "user_credentials",
            {"user_id": row["id"], "password_hash": auth_service.hash_password("password")},
        )
        return User(**row)

    def update_user(self, user_id: str, payload: UserUpdate) -> User:
        fields = payload.model_dump(exclude_unset=True)
        if not fields:
            user = self._single(self.client.table("users").select("*").eq("id", user_id))
            if not user:
                raise KeyError(user_id)
            return User(**user)
        self._execute(self.client.table("users").update(fields).eq("id", user_id))
        user = self._single(self.client.table("users").select("*").eq("id", user_id))
        if not user:
            raise KeyError(user_id)
        return User(**user)

    def delete_user(self, user_id: str) -> None:
        self._execute(self.client.table("users").delete().eq("id", user_id))
        # Cascade cleanup for vehicles/passes to mimic mock behavior
        self._execute(self.client.table("vehicles").delete().eq("user_id", user_id))
        self._execute(self.client.table("passes").delete().eq("user_id", user_id))

    # ------------------------------------------------------------------
    # Vehicles
    # ------------------------------------------------------------------
    def list_vehicles(self) -> List[Vehicle]:
        data = self._execute(self.client.table("vehicles").select("*"))
        return [Vehicle(**row) for row in data]

    def create_vehicle(self, payload: VehicleCreate) -> Vehicle:
        body = payload.model_dump(exclude={"id"})
        body["id"] = payload.id or self._generate_id("VEH")
        row = self._insert_row("vehicles", body)
        return Vehicle(**row)

    def update_vehicle(self, vehicle_id: str, payload: VehicleUpdate) -> Vehicle:
        fields = payload.model_dump(exclude_unset=True)
        self._execute(self.client.table("vehicles").update(fields).eq("id", vehicle_id))
        data = self._single(self.client.table("vehicles").select("*").eq("id", vehicle_id))
        if not data:
            raise KeyError(vehicle_id)
        return Vehicle(**data)

    def delete_vehicle(self, vehicle_id: str) -> None:
        self._execute(self.client.table("vehicles").delete().eq("id", vehicle_id))

    # ------------------------------------------------------------------
    # Passes
    # ------------------------------------------------------------------
    def list_passes(self) -> List[Pass]:
        data = self._execute(self.client.table("passes").select("*"))
        return [Pass(**row) for row in data]

    def create_pass(self, payload: PassCreate) -> Pass:
        user = self.get_user(payload.user_id)
        if not user:
            raise KeyError(payload.user_id)
        starts_at = payload.starts_at or self._now()
        return self._issue_pass_row(
            pass_id=payload.id,
            user_id=user.id,
            role=payload.role,
            plan_type=payload.plan_type,
            starts_at=starts_at,
        )

    def update_pass(self, pass_id: str, payload: PassUpdate) -> Pass:
        fields = payload.model_dump(exclude_unset=True, mode="json")
        current = self._single(self.client.table("passes").select("*").eq("id", pass_id))
        if not current:
            raise KeyError(pass_id)
        plan_type = fields.pop("plan_type", None)
        starts_at = fields.pop("starts_at", None)
        if plan_type or starts_at:
            base_plan = plan_type or current["plan_type"]
            base_start = starts_at or self._now().isoformat()
            parsed_start = datetime.fromisoformat(base_start) if isinstance(base_start, str) else base_start
            valid_from, valid_to, plan = compute_validity_window(base_plan, starts_at=parsed_start)
            fields.update(
                {
                    "plan_type": plan.plan_type,
                    "valid_from": valid_from.isoformat(),
                    "valid_to": valid_to.isoformat(),
                    "price_rm": plan.price_rm,
                    "is_paid": False,
                    "paid_at": None,
                }
            )
            self._create_notification(
                current["user_id"],
                f"{plan.label} pass updated. Pay RM {plan.price_rm:.2f} via wallet.",
            )
        if fields:
            self._execute(self.client.table("passes").update(fields).eq("id", pass_id))
        data = self._single(self.client.table("passes").select("*").eq("id", pass_id))
        if not data:
            raise KeyError(pass_id)
        return Pass(**data)

    def delete_pass(self, pass_id: str) -> None:
        self._execute(self.client.table("passes").delete().eq("id", pass_id))

    def get_latest_pass(self, user_id: str) -> Optional[Pass]:
        row = self._single(
            self.client.table("passes")
            .select("*")
            .eq("user_id", user_id)
            .order("valid_to", desc=True)
        )
        return Pass(**row) if row else None

    def list_pass_applications(self, status: Optional[str] = None) -> List[PassApplication]:
        query = self.client.table("pass_applications").select("*").order("submitted_at", desc=True)
        if status:
            query = query.eq("status", status)
        rows = self._execute(query)
        return [self._pass_application_from_row(row) for row in rows]

    def review_pass_application(self, app_id: str, payload: PassApplicationDecision) -> PassApplication:
        application_row = self._single(self.client.table("pass_applications").select("*").eq("id", app_id))
        if not application_row:
            raise KeyError(app_id)
        if application_row["status"] != "pending":
            return self._pass_application_from_row(application_row)
        reviewer_id = payload.reviewer_id
        review_note = payload.note
        if reviewer_id and not self.get_user(reviewer_id):
            logger.warning("Reviewer %s not found in users table; storing note only", reviewer_id)
            review_note = f"{review_note.strip() if review_note else ''} (Reviewer: {reviewer_id})".strip()
            reviewer_id = None
        now_iso = self._now().isoformat()
        update_fields = {
            "status": payload.status,
            "reviewer_id": reviewer_id,
            "review_note": review_note,
            "reviewed_at": now_iso,
        }
        self._execute(self.client.table("pass_applications").update(update_fields).eq("id", app_id))
        updated_row = self._single(self.client.table("pass_applications").select("*").eq("id", app_id))
        application = self._pass_application_from_row(updated_row)
        if payload.status == "approved":
            self._issue_pass_row(
                pass_id=None,
                user_id=application.user_id,
                role=application.role,
                plan_type=application.plan_type,
                starts_at=self._now(),
            )
        else:
            self._create_notification(application.user_id, payload.note or "Pass application rejected")
        return application

    def _issue_pass_row(
        self,
        *,
        pass_id: Optional[str],
        user_id: str,
        role: str,
        plan_type: str,
        starts_at: datetime,
    ) -> Pass:
        valid_from, valid_to, plan = compute_validity_window(plan_type, starts_at=starts_at)
        target_id = pass_id or self._generate_id("PASS")
        body = {
            "id": target_id,
            "user_id": user_id,
            "role": role,
            "plan_type": plan.plan_type,
            "valid_from": valid_from.isoformat(),
            "valid_to": valid_to.isoformat(),
            "price_rm": plan.price_rm,
            "is_paid": False,
            "paid_at": None,
        }
        row = self._insert_row("passes", body)
        self._create_notification(user_id, f"{plan.label} pass issued. Pay RM {plan.price_rm:.2f} via wallet.")
        return Pass(**row)

    # ------------------------------------------------------------------
    # Access events
    # ------------------------------------------------------------------
    def list_access_events(self, limit: int = 50) -> List[AccessEvent]:
        cached = redis_cache.list_json(CacheKeys.access_events(), limit)
        if cached:
            return [AccessEvent(**row) for row in cached]
        data = self._execute(
            self.client.table("access_events").select("*").order("timestamp", desc=True).limit(limit)
        )
        return [AccessEvent(**row) for row in data]

    def add_access_event(self, payload: AccessEventBase) -> AccessEvent:
        body = payload.model_dump()
        body["id"] = self._generate_id("EVT")
        body["timestamp"] = self._now().isoformat()
        row = self._insert_row("access_events", body)
        event = AccessEvent(**row)
        redis_cache.push_json(CacheKeys.access_events(), event.model_dump(mode="json"), max_length=100)
        return event

    def find_user_by_plate(self, plate_text: str) -> Tuple[Optional[User], Optional[Vehicle]]:
        normalized = self._normalize_plate(plate_text)
        for vehicle in self.list_vehicles():
            if self._normalize_plate(vehicle.plate_text) == normalized:
                user_data = self._single(self.client.table("users").select("*").eq("id", vehicle.user_id))
                user = User(**user_data) if user_data else None
                return user, vehicle
        return None, None

    # ------------------------------------------------------------------
    # Gates
    # ------------------------------------------------------------------
    def list_gates(self) -> List[Gate]:
        data = self._execute(self.client.table("gates").select("*").order("name"))
        return [Gate(**row) for row in data]

    def create_gate(self, payload: GateCreate) -> Gate:
        body = payload.model_dump(exclude={"id"})
        body["id"] = payload.id or self._generate_id("GTE")
        body["slug"] = body["slug"].lower()
        row = self._insert_row("gates", body)
        return Gate(**row)

    def update_gate(self, gate_id: str, payload: GateUpdate) -> Gate:
        fields = payload.model_dump(exclude_unset=True)
        if "slug" in fields and fields["slug"]:
            fields["slug"] = fields["slug"].lower()
        self._execute(self.client.table("gates").update(fields).eq("id", gate_id))
        data = self._single(self.client.table("gates").select("*").eq("id", gate_id))
        if not data:
            raise KeyError(gate_id)
        return Gate(**data)

    def delete_gate(self, gate_id: str) -> None:
        self._execute(self.client.table("gates").delete().eq("id", gate_id))

    def get_gate(self, gate_id: str) -> Optional[Gate]:
        row = self._single(self.client.table("gates").select("*").eq("id", gate_id))
        return Gate(**row) if row else None

    def get_gate_by_slug(self, slug: str) -> Optional[Gate]:
        row = self._single(self.client.table("gates").select("*").eq("slug", slug.lower()))
        return Gate(**row) if row else None

    # ------------------------------------------------------------------
    # Guest sessions / payments
    # ------------------------------------------------------------------
    def list_guest_sessions(self) -> List[GuestSession]:
        data = self._execute(self.client.table("guest_sessions").select("*").order("start_time", desc=True))
        return [GuestSession(**row) for row in data]

    def find_guest_session_by_plate(self, plate_text: str, status: Optional[str] = None) -> Optional[GuestSession]:
        normalized = plate_text.upper()
        cached = redis_cache.get_json(CacheKeys.guest_session(normalized))
        if cached:
            session = GuestSession(**cached)
            if status is None or session.status == status:
                return session
        query = self.client.table("guest_sessions").select("*").eq("plate_text", normalized)
        if status:
            query = query.eq("status", status)
        data = self._single(query.order("start_time", desc=True))
        if not data:
            return None
        session = GuestSession(**data)
        self._cache_guest_session(session)
        return session

    def open_guest_session(self, payload: GuestSessionCreate) -> GuestSession:
        body = {
            "id": self._generate_id("GST"),
            "plate_text": payload.plate_text.upper(),
            "start_time": self._now().isoformat(),
            "status": "open",
        }
        row = self._insert_row("guest_sessions", body)
        session = GuestSession(**row)
        self._cache_guest_session(session)
        return session

    def close_guest_session(self, session_id: str) -> GuestSession:
        session = self._get_guest_session(session_id)
        if session.status != "open":
            return session
        end_time = self._now()
        minutes = max(1, int((end_time - session.start_time).total_seconds() // 60))
        fee = self.compute_guest_fee(minutes)
        update_fields = {
            "end_time": end_time.isoformat(),
            "minutes": minutes,
            "fee": round(fee, 2),
            "status": "closed",
        }
        self._execute(self.client.table("guest_sessions").update(update_fields).eq("id", session_id))
        updated_row = self._single(self.client.table("guest_sessions").select("*").eq("id", session_id))
        if not updated_row:
            raise KeyError(session_id)
        updated = GuestSession(**updated_row)
        self._cache_guest_session(updated)
        return updated

    def pay_guest_session(self, payload: GuestPaymentRequest) -> Payment:
        session = self._get_guest_session(payload.session_id)
        minutes = session.minutes or max(1, int((self._now() - session.start_time).total_seconds() // 60))
        fee = payload.amount or session.fee or self.compute_guest_fee(minutes)
        update_fields = {
            "end_time": session.end_time.isoformat() if session.end_time else self._now().isoformat(),
            "minutes": session.minutes or minutes,
            "fee": round(fee, 2),
            "status": "paid",
        }
        self._execute(self.client.table("guest_sessions").update(update_fields).eq("id", session.id))
        updated_row = self._single(self.client.table("guest_sessions").select("*").eq("id", session.id))
        if not updated_row:
            raise KeyError(session.id)
        updated_session = GuestSession(**updated_row)
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
        self._cache_guest_session(updated_session)
        return payment

    def list_payments(self) -> List[Payment]:
        data = self._execute(self.client.table("payments").select("*").order("timestamp", desc=True))
        return [Payment(**row) for row in data]

    # ------------------------------------------------------------------
    # Guest rates
    # ------------------------------------------------------------------
    def get_guest_rate(self) -> GuestRateResponse:
        query = self.client.table("guest_rates").select("*").eq("id", self.RATE_SINGLETON_ID)
        data = self._single(query)
        if not data:
            return GuestRateResponse(**self._guest_rate_cache)
        self._guest_rate_cache.update({"base_rate": data["base_rate"], "per_minute_rate": data["per_minute_rate"]})
        return GuestRateResponse(**self._guest_rate_cache)

    def update_guest_rate(self, payload: GuestRateUpdate) -> GuestRateResponse:
        body = {
            "id": self.RATE_SINGLETON_ID,
            "base_rate": payload.base_rate,
            "per_minute_rate": payload.per_minute_rate,
        }
        self._execute(self.client.table("guest_rates").upsert(body))
        self._guest_rate_cache.update(body)
        return GuestRateResponse(base_rate=body["base_rate"], per_minute_rate=body["per_minute_rate"])

    def compute_guest_fee(self, minutes: int) -> float:
        rate = self.get_guest_rate()
        return rate.base_rate + rate.per_minute_rate * max(0, minutes)

    # ------------------------------------------------------------------
    # Client portal / mobile flows
    # ------------------------------------------------------------------
    def register_client(self, payload: ClientRegistrationRequest) -> ClientRegistrationResponse:
        if payload.role == "guest":
            raise ValueError("Guest role cannot receive parking passes")
        existing = self._find_user_by_email(payload.email)
        if existing:
            user = existing
            if payload.role != "guest" and existing.role != payload.role:
                user = self.update_user(existing.id, UserUpdate(role=payload.role))
        else:
            user = self.create_user(
                UserCreate(
                    name=payload.name,
                    email=payload.email,
                    phone=payload.phone,
                    role=payload.role,
                    programme=payload.programme,
                )
            )
        registration = self._ensure_client_registration(user.id, status="pending")
        profile = self._ensure_client_profile(user.id, status="pending")
        pass_row = self._single(self.client.table("passes").select("*").eq("user_id", user.id))
        if pass_row:
            parking_pass = Pass(**pass_row)
        else:
            parking_pass = None
        vehicles = [vehicle for vehicle in self.list_vehicles() if vehicle.user_id == user.id]
        existing_plates: set[str] = set()
        for vehicle in vehicles:
            normalized_plate = self._normalize_plate(vehicle.plate_text)
            if normalized_plate:
                existing_plates.add(normalized_plate)
        for plate in payload.vehicles:
            normalized = self._normalize_plate(plate)
            if not normalized or normalized in existing_plates:
                continue
            created = self.create_vehicle(VehicleCreate(user_id=user.id, plate_text=normalized))
            vehicles.append(created)
            existing_plates.add(normalized)
        registration = registration.model_copy(update={"status": "pending"})
        self._client_registrations[registration.id] = registration
        self._client_profiles[user.id] = profile.model_copy(update={"status": "pending", "updated_at": self._now()})
        normalized_vehicles: List[str] = []
        seen: set[str] = set()
        for plate in payload.vehicles:
            normalized = self._normalize_plate(plate)
            if normalized and normalized not in seen:
                normalized_vehicles.append(normalized)
                seen.add(normalized)
        application_body = {
            "id": self._generate_id("APP"),
            "user_id": user.id,
            "role": payload.role,
            "plan_type": payload.plan_type,
            "vehicles": normalized_vehicles,
            "status": "pending",
            "submitted_at": self._now().isoformat(),
        }
        application_row = self._insert_row("pass_applications", application_body)
        application = self._pass_application_from_row(application_row)
        self._create_notification(user.id, "Pass application submitted. Await admin review.")
        return ClientRegistrationResponse(
            registration=registration,
            profile=self._client_profiles[user.id],
            user=user,
            pass_info=parking_pass,
            vehicles=vehicles,
            pass_application=application,
        )

    def signup_portal_user(self, payload: SignupRequest) -> AuthResponse:
        if self._find_user_by_email(payload.email):
            raise ValueError("Email already registered")
        user_id = self._generate_id("USR")
        body = {
            "id": user_id,
            "name": payload.name,
            "email": payload.email,
            "phone": payload.phone,
            "role": "guest",
            "programme": payload.programme,
            "wallet_balance": 0,
        }
        self._insert_row("users", body)
        self._insert_row(
            "user_credentials",
            {"user_id": user_id, "password_hash": auth_service.hash_password(payload.password)},
        )
        user = User(**body)
        token = auth_service.create_token({"user_id": user_id})
        return AuthResponse(token=token, user=user)

    def login_portal_user(self, payload: LoginRequest) -> AuthResponse:
        identifier = payload.identifier
        query = (
            self.client.table("users")
            .select("*")
            .or_(f"email.eq.{identifier},id.eq.{identifier},name.ilike.{identifier}")
            .limit(1)
        )
        row = self._single(query)
        if not row:
            raise ValueError("User not found")
        credentials = self._single(self.client.table("user_credentials").select("*").eq("user_id", row["id"]))
        if not credentials or not auth_service.verify_password(payload.password, credentials["password_hash"]):
            raise ValueError("Invalid credentials")
        user = User(**row)
        token = auth_service.create_token({"user_id": user.id})
        return AuthResponse(token=token, user=user)

    def get_client_summary(self, user_id: str) -> ClientSummary:
        user = self.get_user(user_id)
        if not user:
            raise KeyError(user_id)
        pass_row = self._single(self.client.table("passes").select("*").eq("user_id", user_id))
        pass_info = Pass(**pass_row) if pass_row else None
        vehicles = [Vehicle(**row) for row in self._execute(self.client.table("vehicles").select("*").eq("user_id", user_id))]
        profile = self._ensure_client_profile(user_id, status="active" if user.role != "guest" else "pending")
        wallet = self._wallet_snapshot(user_id)
        guest_sessions = self._guest_sessions_for_user(vehicles)
        upgrades = self._fetch_role_upgrades(user_id)
        application_rows = self._execute(
            self.client.table("pass_applications").select("*").eq("user_id", user_id).order("submitted_at", desc=True)
        )
        applications = [self._pass_application_from_row(row) for row in application_rows]
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
        charge = touchngo_gateway.charge_wallet_top_up(user_id=user_id, amount_rm=payload.amount)
        self._apply_wallet_delta(
            user_id,
            delta=payload.amount,
            txn_type="top_up",
            description=f"Wallet top-up ({payload.source})",
            source=payload.source,
        )
        self._record_payment(amount=payload.amount, processor=charge.processor, reference=charge.transaction_id)
        return self._wallet_activity(user_id)

    def get_wallet_activity(self, user_id: str) -> ClientWalletActivity:
        return self._wallet_activity(user_id)

    def submit_role_upgrade(self, user_id: str, payload: RoleUpgradeSubmit) -> RoleUpgradeRequest:
        body = {
            "id": self._generate_id("URQ"),
            "user_id": user_id,
            "target_role": payload.target_role,
            "reason": payload.reason,
            "attachments": payload.attachments,
            "status": "pending",
            "submitted_at": self._now().isoformat(),
        }
        row = self._insert_row("role_upgrade_requests", body)
        profile = self._ensure_client_profile(user_id)
        self._client_profiles[user_id] = profile.model_copy(update={"status": "pending", "updated_at": self._now()})
        return RoleUpgradeRequest(**row)

    def list_role_upgrades(self, status: Optional[str] = None) -> List[RoleUpgradeRequest]:
        query = self.client.table("role_upgrade_requests").select("*").order("submitted_at", desc=True)
        if status:
            query = query.eq("status", status)
        rows = self._execute(query)
        return [RoleUpgradeRequest(**row) for row in rows]

    def review_role_upgrade(self, request_id: str, payload: RoleUpgradeDecision) -> RoleUpgradeRequest:
        row = self._single(self.client.table("role_upgrade_requests").select("*").eq("id", request_id))
        if not row:
            raise KeyError(request_id)
        update_fields = {
            "status": payload.status,
            "reviewer_id": payload.reviewer_id,
            "reviewed_at": self._now().isoformat(),
        }
        self._execute(self.client.table("role_upgrade_requests").update(update_fields).eq("id", request_id))
        if payload.status == "approved":
            self._execute(self.client.table("users").update({"role": row["target_role"]}).eq("id", row["user_id"]))
            self._execute(self.client.table("passes").update({"role": row["target_role"]}).eq("user_id", row["user_id"]))
        message = payload.note or f"Role upgrade to {row['target_role']} {payload.status.upper()}"
        self._create_notification(row["user_id"], message)
        row.update(update_fields)
        return RoleUpgradeRequest(**row)

    def get_parking_overview(self) -> ParkingOverview:
        rows = self._execute(self.client.table("parking_venues").select("*").order("name"))
        venues = [
            ParkingVenueStatus(
                id=row["id"],
                name=row["name"],
                capacity=row["capacity"],
                occupied=row["occupied"],
                percent=round((row["occupied"] / row["capacity"]) * 100, 1) if row["capacity"] else 0.0,
            )
            for row in rows
        ]
        return ParkingOverview(venues=venues)

    def list_parking_venues(self) -> List[ParkingVenueStatus]:
        rows = self._execute(self.client.table("parking_venues").select("*").order("name"))
        return [
            ParkingVenueStatus(
                id=row["id"],
                name=row["name"],
                capacity=row["capacity"],
                occupied=row["occupied"],
                percent=round((row["occupied"] / row["capacity"]) * 100, 1) if row["capacity"] else 0.0,
            )
            for row in rows
        ]

    def create_parking_venue(self, payload: ParkingVenueCreate) -> ParkingVenueStatus:
        body = {
            "id": payload.id or self._generate_id("VEN"),
            "name": payload.name,
            "capacity": max(0, payload.capacity),
        }
        occupied = max(0, payload.occupied or 0)
        body["occupied"] = min(body["capacity"], occupied)
        row = self._insert_row("parking_venues", body)
        row["percent"] = round((row["occupied"] / row["capacity"]) * 100, 1) if row["capacity"] else 0.0
        return ParkingVenueStatus(**row)

    def update_parking_venue(self, venue_id: str, payload: ParkingVenueUpdate) -> ParkingVenueStatus:
        venue_row = self._single(self.client.table("parking_venues").select("*").eq("id", venue_id))
        if not venue_row:
            raise KeyError(venue_id)
        name = payload.name if payload.name is not None else venue_row["name"]
        capacity = payload.capacity if payload.capacity is not None else venue_row["capacity"]
        occupied = payload.occupied if payload.occupied is not None else venue_row["occupied"]
        capacity = max(0, capacity)
        occupied = max(0, min(capacity, occupied))
        update_fields = {"name": name, "capacity": capacity, "occupied": occupied}
        self._execute(self.client.table("parking_venues").update(update_fields).eq("id", venue_id))
        row = self._single(self.client.table("parking_venues").select("*").eq("id", venue_id))
        if not row:
            raise KeyError(venue_id)
        row["percent"] = round((row["occupied"] / row["capacity"]) * 100, 1) if row["capacity"] else 0.0
        return ParkingVenueStatus(**row)

    def delete_parking_venue(self, venue_id: str) -> None:
        row = self._single(self.client.table("parking_venues").select("id").eq("id", venue_id))
        if not row:
            raise KeyError(venue_id)
        self._execute(self.client.table("parking_venues").delete().eq("id", venue_id))
        self._execute(
            self.client.table("gates")
            .update({"parking_venue_id": None, "parking_direction": None})
            .eq("parking_venue_id", venue_id)
        )

    def record_parking_event(self, payload: ParkingEventRequest) -> ParkingVenueStatus:
        venue_row = self._single(self.client.table("parking_venues").select("*").eq("id", payload.venue_id))
        if not venue_row:
            raise KeyError(payload.venue_id)
        delta = 1 if payload.direction == "entry" else -1
        occupied = max(0, min(venue_row["capacity"], venue_row["occupied"] + delta))
        self._execute(self.client.table("parking_venues").update({"occupied": occupied}).eq("id", payload.venue_id))
        self._insert_row(
            "parking_events",
            {
                "id": self._generate_id("PEV"),
                "venue_id": payload.venue_id,
                "direction": payload.direction,
                "delta": delta,
            },
        )
        venue_row["occupied"] = occupied
        venue_row["percent"] = round((occupied / venue_row["capacity"]) * 100, 1) if venue_row["capacity"] else 0.0
        return ParkingVenueStatus(**venue_row)

    def lookup_guest_session(self, session_id: Optional[str] = None, plate_text: Optional[str] = None) -> GuestSessionLookupResponse:
        if not session_id and not plate_text:
            raise KeyError("guest_session_lookup_requires_identifier")
        return self._resolve_guest_session(session_id=session_id, plate_text=plate_text)

    def client_pay_guest_session(self, payload: ClientGuestPaymentRequest) -> Payment:
        if not payload.session_id:
            raise ValueError("session_id required")
        amount_to_pay: Optional[float] = None
        if payload.payment_source == "wallet" and not payload.user_id:
            raise ValueError("user_id required for wallet payments")
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
    def _record_payment(
        self,
        *,
        amount: float,
        processor: str,
        reference: Optional[str],
        session_id: Optional[str] = None,
        pass_id: Optional[str] = None,
    ) -> Payment:
        body = {
            "id": self._generate_id("PAY"),
            "amount": round(amount, 2),
            "status": "succeeded",
            "processor": processor,
            "timestamp": self._now().isoformat(),
            "currency": settings.currency_code,
            "reference": reference,
        }
        if session_id:
            body["session_id"] = session_id
        if pass_id:
            body["pass_id"] = pass_id
        payment_row = self._insert_row("payments", body)
        return Payment(**payment_row)

    def _cache_guest_session(self, session: GuestSession) -> None:
        key = CacheKeys.guest_session(session.plate_text)
        if session.status == "open":
            redis_cache.set_json(key, session.model_dump(mode="json"), ttl=4 * 60 * 60)
        else:
            redis_cache.delete(key)

    def _get_guest_session(self, session_id: str) -> GuestSession:
        data = self._single(self.client.table("guest_sessions").select("*").eq("id", session_id))
        if not data:
            raise KeyError(session_id)
        return GuestSession(**data)

    def _find_user_by_email(self, email: str) -> Optional[User]:
        row = self._single(self.client.table("users").select("*").eq("email", email))
        return User(**row) if row else None

    def _ensure_client_registration(self, user_id: str, status: str = "pending") -> ClientRegistration:
        for registration in self._client_registrations.values():
            if registration.user_id == user_id:
                return registration
        registration = ClientRegistration(
            id=self._generate_id("REG"),
            user_id=user_id,
            status=status,
            submitted_at=self._now(),
        )
        self._client_registrations[registration.id] = registration
        return registration

    def _ensure_client_profile(self, user_id: str, status: str = "pending") -> ClientProfile:
        profile = self._client_profiles.get(user_id)
        if profile:
            return profile
        registration = self._ensure_client_registration(user_id, status=status)
        now = self._now()
        profile = ClientProfile(
            user_id=user_id,
            registration_id=registration.id,
            status=status,
            guest_pin=f"{randint(1000, 9999)}",
            wallet_balance=0.0,
            created_at=now,
            updated_at=now,
        )
        self._client_profiles[user_id] = profile
        self._wallet_transactions.setdefault(user_id, [])
        return profile

    def _wallet_snapshot(self, user_id: str) -> ClientWallet:
        user = self.get_user(user_id)
        if not user:
            raise KeyError(user_id)
        transactions = self._wallet_transactions_for_user(user_id, limit=20)
        last_top_up = next((txn.timestamp for txn in transactions if txn.type == "top_up"), None)
        return ClientWallet(
            user_id=user_id,
            balance=round(user.wallet_balance or 0.0, 2),
            last_top_up=last_top_up,
            currency=settings.currency_code,
        )

    def _wallet_activity(self, user_id: str) -> ClientWalletActivity:
        wallet = self._wallet_snapshot(user_id)
        transactions = self._wallet_transactions_for_user(user_id, limit=20)
        return ClientWalletActivity(wallet=wallet, transactions=transactions)

    def _wallet_transactions_for_user(self, user_id: str, limit: int = 20) -> List[WalletTransaction]:
        rows = (
            self.client.table("wallet_transactions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []
        return [
            WalletTransaction(
                id=row["id"],
                user_id=row["user_id"],
                amount=float(row["amount"]),
                type=row["type"],
                description=row["description"],
                timestamp=row["created_at"],
                source=row["source"],
            )
            for row in rows
        ]

    def _pass_application_from_row(self, row: Dict[str, Any]) -> PassApplication:
        payload = dict(row)
        payload["vehicles"] = payload.get("vehicles") or []
        return PassApplication(**payload)

    def _apply_wallet_delta(
        self,
        user_id: str,
        *,
        delta: float,
        txn_type: str,
        description: str,
        source: str,
    ) -> WalletTransaction:
        user = self.get_user(user_id)
        if not user:
            raise KeyError(user_id)
        new_balance = round((user.wallet_balance or 0.0) + delta, 2)
        if new_balance < -1e-6:
            raise ValueError("Insufficient wallet balance")
        self._execute(self.client.table("users").update({"wallet_balance": new_balance}).eq("id", user_id))
        txn_body = {
            "id": self._generate_id("TXN"),
            "user_id": user_id,
            "amount": round(delta, 2),
            "type": txn_type,
            "description": description,
            "source": source,
        }
        row = self._insert_row("wallet_transactions", txn_body)
        return WalletTransaction(
            id=row["id"],
            user_id=row["user_id"],
            amount=float(row["amount"]),
            type=row["type"],
            description=row["description"],
            timestamp=row["created_at"],
            source=row["source"],
        )

    def pay_pass_invoice(self, user_id: str, pass_id: str) -> Pass:
        pass_row = self._single(self.client.table("passes").select("*").eq("id", pass_id))
        if not pass_row:
            raise KeyError(pass_id)
        if pass_row["user_id"] != user_id:
            raise ValueError("Pass does not belong to user")
        if pass_row.get("is_paid"):
            return Pass(**pass_row)
        price = float(pass_row["price_rm"])
        txn = self._apply_wallet_delta(
            user_id,
            delta=-price,
            txn_type="pass_payment",
            description=f"Pass {pass_row['plan_type']}",
            source="wallet",
        )
        update_fields = {"is_paid": True, "paid_at": self._now().isoformat()}
        self._execute(self.client.table("passes").update(update_fields).eq("id", pass_id))
        updated = self._single(self.client.table("passes").select("*").eq("id", pass_id))
        self._record_payment(amount=price, processor="wallet", reference=txn.id, pass_id=pass_id)
        self._create_notification(user_id, f"Pass payment received: RM {price:.2f}")
        return Pass(**updated)

    def _guest_sessions_for_user(self, vehicles: List[Vehicle]) -> List[GuestSession]:
        if not vehicles:
            return []
        sessions: List[GuestSession] = []
        for vehicle in vehicles:
            data = self._execute(
                self.client.table("guest_sessions")
                .select("*")
                .eq("plate_text", vehicle.plate_text.upper())
                .order("start_time", desc=True)
            )
            sessions.extend(GuestSession(**row) for row in data)
        sessions.sort(key=lambda s: s.start_time, reverse=True)
        return sessions

    def _fetch_role_upgrades(self, user_id: str) -> List[RoleUpgradeRequest]:
        rows = (
            self.client.table("role_upgrade_requests")
            .select("*")
            .eq("user_id", user_id)
            .order("submitted_at", desc=True)
            .execute()
        ).data or []
        return [RoleUpgradeRequest(**row) for row in rows]

    def _resolve_guest_session(self, session_id: Optional[str], plate_text: Optional[str]) -> GuestSessionLookupResponse:
        session: Optional[GuestSession] = None
        if session_id:
            try:
                session = self._get_guest_session(session_id)
            except KeyError:
                session = None
        if not session and plate_text:
            session = self.find_guest_session_by_plate(plate_text, status=None)
        if not session:
            identifier = session_id or plate_text or "session"
            raise KeyError(identifier)
        minutes = session.minutes or max(1, int((self._now() - session.start_time).total_seconds() // 60))
        fee = session.fee or self.compute_guest_fee(minutes)
        return GuestSessionLookupResponse(session=session, amount_due=round(fee, 2))

    def list_notifications(self, user_id: str) -> List[Notification]:
        rows = (
            self.client.table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        ).data or []
        return [self._notification_from_row(row) for row in rows]

    def acknowledge_notification(self, user_id: str, notification_id: str) -> Notification:
        row = (
            self.client.table("notifications")
            .select("*")
            .eq("id", notification_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        ).data
        if not row:
            raise KeyError(notification_id)
        self._execute(
            self.client.table("notifications")
            .update({"is_read": True})
            .eq("id", notification_id)
        )
        row[0]["is_read"] = True
        return self._notification_from_row(row[0])

    def _create_notification(self, user_id: str, message: str) -> Notification:
        body = {
            "id": self._generate_id("NTF"),
            "user_id": user_id,
            "message": message,
            "is_read": False,
        }
        row = self._insert_row("notifications", body)
        return self._notification_from_row(row)

    def _notification_from_row(self, row: Dict[str, Any]) -> Notification:
        """Best-effort Notification construction even if module import order changes."""
        try:
            notification_model = Notification
        except NameError:  # pragma: no cover - defensive for import edge cases
            from app.schemas import Notification as NotificationModel

            notification_model = NotificationModel
        payload = dict(row)
        payload.setdefault("created_at", self._now())
        payload.setdefault("is_read", False)
        return notification_model(**payload)


__all__ = ["SupabaseStore"]
