-- Auth credentials table
create table if not exists public.user_credentials (
    user_id text primary key references public.users (id) on delete cascade,
    password_hash text not null,
    created_at timestamptz not null default now()
);

-- Wallet transactions ledger
create table if not exists public.wallet_transactions (
    id text primary key,
    user_id text not null references public.users (id) on delete cascade,
    amount numeric(12,2) not null,
    type text not null default 'adjustment',
    description text not null default 'adjustment',
    source text not null default 'system',
    created_at timestamptz not null default now()
);
create index if not exists wallet_transactions_user_idx on public.wallet_transactions (user_id);

-- Parking metadata
create table if not exists public.parking_floors (
    id text primary key,
    venue text not null,
    name text not null,
    capacity integer not null default 0,
    occupied integer not null default 0
);

create table if not exists public.parking_events (
    id text primary key,
    floor_id text not null references public.parking_floors (id) on delete cascade,
    direction text not null check (direction in ('entry','exit')),
    delta integer not null,
    created_at timestamptz not null default now()
);
create index if not exists parking_events_floor_idx on public.parking_events (floor_id);

create table if not exists public.role_upgrade_requests (
    id text primary key,
    user_id text not null references public.users (id) on delete cascade,
    target_role text not null,
    reason text not null,
    attachments jsonb not null default '[]'::jsonb,
    status text not null default 'pending',
    submitted_at timestamptz not null default now(),
    reviewed_at timestamptz null,
    reviewer_id text null references public.users (id)
);
create index if not exists role_upgrade_requests_user_idx on public.role_upgrade_requests (user_id);

create table if not exists public.notifications (
    id text primary key,
    user_id text not null references public.users (id) on delete cascade,
    message text not null,
    created_at timestamptz not null default now(),
    is_read boolean not null default false
);
create index if not exists notifications_user_idx on public.notifications (user_id, is_read);

alter table public.users
    add column wallet_balance numeric(12,2) not null default 0;
