from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class PassPlanDefinition:
    plan_type: str
    label: str
    duration_days: int
    price_rm: float


PASS_PLANS: Dict[str, PassPlanDefinition] = {
    "short_semester": PassPlanDefinition(
        plan_type="short_semester",
        label="Short Semester (50 days)",
        duration_days=50,
        price_rm=30.0,
    ),
    "long_semester": PassPlanDefinition(
        plan_type="long_semester",
        label="Long Semester (100 days)",
        duration_days=100,
        price_rm=50.0,
    ),
    "annual": PassPlanDefinition(
        plan_type="annual",
        label="Annual (365 days)",
        duration_days=365,
        price_rm=120.0,
    ),
}


def list_pass_plans() -> Iterable[PassPlanDefinition]:
    return PASS_PLANS.values()


def get_pass_plan(plan_type: str) -> PassPlanDefinition:
    try:
        return PASS_PLANS[plan_type]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Unknown pass plan {plan_type}") from exc


def compute_validity_window(
    plan_type: str,
    *,
    starts_at: datetime | None = None,
) -> Tuple[datetime, datetime, PassPlanDefinition]:
    plan = get_pass_plan(plan_type)
    start = starts_at or datetime.now(timezone.utc)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(days=plan.duration_days)
    return start, end, plan
