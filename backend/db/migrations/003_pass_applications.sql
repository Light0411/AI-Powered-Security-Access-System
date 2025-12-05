create table if not exists public.pass_applications (
    id text primary key,
    user_id text not null references public.users (id) on delete cascade,
    role text not null,
    plan_type text not null,
    vehicles text[] not null default '{}'::text[],
    status text not null default 'pending' check (status in ('pending','approved','rejected')),
    reviewer_id text null references public.users (id),
    review_note text null,
    submitted_at timestamptz not null default now(),
    reviewed_at timestamptz null
);

create index if not exists pass_applications_user_idx on public.pass_applications (user_id);
create index if not exists pass_applications_status_idx on public.pass_applications (status);

alter table public.passes
    add column if not exists is_paid boolean not null default false;

alter table public.passes
    add column if not exists paid_at timestamptz null;
