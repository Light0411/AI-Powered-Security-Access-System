from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import randint

from app.core.passes import get_pass_plan
from app.schemas import AccessEvent, Gate, GuestSession, Pass, ParkingVenueStatus, Payment, User, Vehicle

NOW = datetime.now(timezone.utc)


def seed_users() -> list[User]:
    return [
        User(
            id="USR-001",
            name="Amina Chancellor",
            email="amina@smartgate.demo",
            phone="+120255501",
            role="admin",
            programme="Security",
            wallet_balance=120.0,
        ),
        User(
            id="USR-002",
            name="Kai Mendes",
            email="kai@smartgate.demo",
            phone="+120255502",
            role="staff",
            programme="Engineering",
            wallet_balance=80.0,
        ),
        User(
            id="USR-003",
            name="Lena Ortiz",
            email="lena@smartgate.demo",
            phone="+120255503",
            role="student",
            programme="Business",
            wallet_balance=40.0,
        ),
    ]


def seed_vehicles() -> list[Vehicle]:
    return [
        Vehicle(id="VEH-001", plate_text="SGT230", user_id="USR-001"),
        Vehicle(id="VEH-002", plate_text="CAMP88", user_id="USR-002"),
        Vehicle(id="VEH-003", plate_text="LEARN9", user_id="USR-003"),
    ]


def seed_passes() -> list[Pass]:
    annual = get_pass_plan("annual")
    long_sem = get_pass_plan("long_semester")
    short_sem = get_pass_plan("short_semester")
    return [
        Pass(
            id="PASS-001",
            user_id="USR-001",
            role="admin",
            plan_type=annual.plan_type,
            valid_from=NOW - timedelta(days=5),
            valid_to=NOW + timedelta(days=annual.duration_days - 5),
            price_rm=annual.price_rm,
        ),
        Pass(
            id="PASS-002",
            user_id="USR-002",
            role="staff",
            plan_type=long_sem.plan_type,
            valid_from=NOW - timedelta(days=3),
            valid_to=NOW + timedelta(days=long_sem.duration_days - 3),
            price_rm=long_sem.price_rm,
        ),
        Pass(
            id="PASS-003",
            user_id="USR-003",
            role="student",
            plan_type=short_sem.plan_type,
            valid_from=NOW - timedelta(days=1),
            valid_to=NOW + timedelta(days=short_sem.duration_days - 1),
            price_rm=short_sem.price_rm,
        ),
    ]


def seed_events() -> list[AccessEvent]:
    base = NOW - timedelta(hours=6)
    events: list[AccessEvent] = []
    plates = ["SGT230", "CAMP88", "LEARN9", "VISIT1"]
    for idx in range(18):
        plate = plates[idx % len(plates)]
        decision = "ALLOW" if plate != "VISIT1" else "GUEST"
        role = "guest" if plate == "VISIT1" else "staff"
        events.append(
            AccessEvent(
                id=f"EVT-{idx:03d}",
                plate_text=plate,
                confidence=round(0.83 + (idx % 4) * 0.03, 2),
                decision=decision,
                role=role,
                reason="Role threshold met" if decision == "ALLOW" else "Guest access",
                gate="outer" if idx % 3 else "inner",
                snapshot_url=None,
                timestamp=base + timedelta(minutes=idx * 10),
            )
        )
    return events


def seed_guest_sessions() -> list[GuestSession]:
    sessions: list[GuestSession] = []
    for idx in range(2):
        start = NOW - timedelta(hours=idx + 1)
        end = start + timedelta(minutes=randint(15, 60))
        fee = 2.5 + 0.75 * randint(15, 60)
        sessions.append(
            GuestSession(
                id=f"GST-{idx:03d}",
                plate_text=f"VISIT{idx+1}",
                start_time=start,
                end_time=end,
                minutes=int((end - start).total_seconds() // 60),
                fee=round(fee, 2),
                status="paid" if idx == 0 else "closed",
            )
        )
    sessions.append(
        GuestSession(
            id="GST-999",
            plate_text="VISITX",
            start_time=NOW - timedelta(minutes=30),
            status="open",
        )
    )
    return sessions


def seed_payments() -> list[Payment]:
    return [
        Payment(
            id="PAY-001",
            amount=12.5,
            status="succeeded",
            processor="mock",
            timestamp=NOW - timedelta(hours=2),
            session_id="GST-000",
            currency="MYR",
            reference="TNG-SEED-0001",
        )
    ]


def seed_gates() -> list[Gate]:
    return [
        Gate(
            id="GATE-OUTER",
            name="Outer Gate",
            slug="outer",
            min_role="guest",
            location="Perimeter",
            is_active=True,
            parking_venue_id="VEN-ATH",
            parking_direction="entry",
        ),
        Gate(
            id="GATE-INNER",
            name="Inner Gate",
            slug="inner",
            min_role="staff",
            location="Campus Core",
            is_active=True,
            parking_venue_id="VEN-ATH",
            parking_direction="exit",
        ),
    ]


def seed_parking_venues() -> list[ParkingVenueStatus]:
    data = [
        ("VEN-ATH", "Athletics Deck", 240, 124),
        ("VEN-ACD", "Academic Core", 180, 96),
        ("VEN-WLC", "Welcome Center", 80, 32),
    ]
    venues: list[ParkingVenueStatus] = []
    for venue_id, name, capacity, occupied in data:
        percent = round((occupied / capacity) * 100, 1) if capacity else 0.0
        venues.append(
            ParkingVenueStatus(
                id=venue_id,
                name=name,
                capacity=capacity,
                occupied=occupied,
                percent=percent,
            )
        )
    return venues
