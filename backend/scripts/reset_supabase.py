"""Utility script to wipe demo data from Supabase tables.

Usage:
    python -m scripts.reset_supabase
"""

from __future__ import annotations

from dataclasses import dataclass

from supabase import Client, create_client

from app.core.config import settings
from app.data import seed
from app.services.auth import auth_service


@dataclass
class TableReset:
    name: str
    filter_column: str = "id"


TABLES: list[TableReset] = [
    TableReset("notifications"),
    TableReset("role_upgrade_requests"),
    TableReset("access_events"),
    TableReset("guest_sessions"),
    TableReset("payments"),
    TableReset("vehicles"),
    TableReset("passes"),
    TableReset("parking_events"),
    TableReset("parking_venues"),
    TableReset("wallet_transactions"),
    TableReset("user_credentials", filter_column="user_id"),
    TableReset("gates"),
    TableReset("guest_rates"),
    TableReset("users"),
]


def truncate_table(client: Client, table: TableReset) -> None:
    # Supabase DELETE must include a filter; use the configured column and delete everything.
    try:
        client.table(table.name).delete().neq(table.filter_column, "").execute()
    except Exception as exc:  # pragma: no cover - depends on remote state
        raise RuntimeError(f"Failed to truncate {table.name}: {exc}") from exc


def reseed_defaults(client: Client) -> None:
    # Repopulate basic demo entities so the web/admin UIs stay functional post-reset.
    for user in seed.seed_users():
        client.table("users").upsert(user.model_dump(mode="json")).execute()
        client.table("user_credentials").upsert(
            {"user_id": user.id, "password_hash": auth_service.hash_password("password")}
        ).execute()
    for vehicle in seed.seed_vehicles():
        client.table("vehicles").upsert(vehicle.model_dump(mode="json")).execute()
    for parking_pass in seed.seed_passes():
        client.table("passes").upsert(parking_pass.model_dump(mode="json")).execute()
    for gate in seed.seed_gates():
        client.table("gates").upsert(gate.model_dump(mode="json")).execute()
    for session in seed.seed_guest_sessions():
        client.table("guest_sessions").upsert(session.model_dump(mode="json")).execute()
    for payment in seed.seed_payments():
        client.table("payments").upsert(payment.model_dump(mode="json")).execute()
    client.table("guest_rates").upsert({"id": "default", "base_rate": seed.NOW.minute / 60.0, "per_minute_rate": 0.75}).execute()
    for venue in seed.seed_parking_venues():
        payload = venue.model_dump(mode="json", exclude={"percent"})
        client.table("parking_venues").upsert(payload).execute()


def main() -> None:
    client = create_client(settings.supabase_url, settings.supabase_key)
    for table in TABLES:
        truncate_table(client, table)
    reseed_defaults(client)
    print("Supabase tables wiped and demo data reseeded.")


if __name__ == "__main__":
    main()
