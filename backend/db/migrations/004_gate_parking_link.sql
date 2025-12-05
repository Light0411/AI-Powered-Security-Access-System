create table if not exists public.parking_venues (
    id text primary key,
    name text not null,
    capacity integer not null default 0,
    occupied integer not null default 0
);

insert into public.parking_venues (id, name, capacity, occupied)
select id, coalesce(name, venue), capacity, occupied
from public.parking_floors
on conflict (id) do nothing;

drop index if exists gates_parking_floor_idx;
drop index if exists parking_events_floor_idx;
alter table if exists public.gates drop column if exists parking_floor_id;

alter table if exists public.gates
    add column if not exists parking_venue_id text references public.parking_venues (id),
    add column if not exists parking_direction text check (parking_direction in ('entry','exit'));

create index if not exists gates_parking_venue_idx on public.gates (parking_venue_id);

alter table if exists public.parking_events
    add column if not exists venue_id text;

update public.parking_events
set venue_id = floor_id
where venue_id is null and floor_id is not null;

alter table if exists public.parking_events
    drop constraint if exists parking_events_floor_id_fkey;

alter table if exists public.parking_events
    add constraint parking_events_venue_id_fkey foreign key (venue_id) references public.parking_venues (id) on delete cascade;

alter table if exists public.parking_events
    alter column venue_id set not null;

create index if not exists parking_events_venue_idx on public.parking_events (venue_id);

alter table if exists public.parking_events drop column if exists floor_id;
