from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import List

from app.schemas import AnalyticsResponse, GateFrequencyPoint, GuestFeePoint

from .datastore import db


def _bucket_timestamp(ts: datetime) -> datetime:
    rounded_minutes = (ts.minute // 15) * 15
    return ts.replace(minute=rounded_minutes, second=0, microsecond=0)


def build_analytics() -> AnalyticsResponse:
    events = db.list_access_events(limit=200)
    gate_counter: dict[datetime, dict[str, int]] = defaultdict(dict)
    for event in events:
        bucket = _bucket_timestamp(event.timestamp)
        gate_counts = gate_counter[bucket]
        gate_counts[event.gate] = gate_counts.get(event.gate, 0) + 1

    gate_frequency: List[GateFrequencyPoint] = [
        GateFrequencyPoint(
            timestamp=ts,
            outer=counts.get("outer", 0),
            inner=counts.get("inner", 0),
        )
        for ts, counts in sorted(gate_counter.items())
    ]

    guest_fee_trend: List[GuestFeePoint] = []
    for session in db.list_guest_sessions():
        if session.fee and session.end_time:
            guest_fee_trend.append(GuestFeePoint(timestamp=session.end_time, fee=session.fee))

    role_distribution = Counter(user.role for user in db.list_users())
    programme_distribution = Counter(user.programme for user in db.list_users())

    vehicle_distribution = Counter()
    users = {user.id: user for user in db.list_users()}
    for vehicle in db.list_vehicles():
        owner_role = users.get(vehicle.user_id).role if vehicle.user_id in users else "guest"
        vehicle_distribution[owner_role] += 1

    sessions = db.list_guest_sessions()
    unpaid = sum(1 for session in sessions if session.status != "paid")
    guest_unpaid_ratio = unpaid / len(sessions) if sessions else 0.0

    if not gate_frequency:
        now = datetime.utcnow()
        gate_frequency.append(GateFrequencyPoint(timestamp=now, outer=0, inner=0))

    if not guest_fee_trend:
        guest_fee_trend.append(GuestFeePoint(timestamp=datetime.utcnow(), fee=0.0))

    return AnalyticsResponse(
        gate_frequency=gate_frequency,
        guest_fee_trend=guest_fee_trend,
        role_distribution=dict(role_distribution),
        programme_distribution=dict(programme_distribution),
        guest_unpaid_ratio=round(guest_unpaid_ratio, 2),
        vehicle_distribution=dict(vehicle_distribution),
    )
