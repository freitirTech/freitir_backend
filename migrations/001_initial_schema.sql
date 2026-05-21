-- ============================================================
-- FREITIR — Phase 1 Schema
-- Run this in: Supabase Dashboard → SQL Editor → New query
-- ============================================================


-- ── CARRIERS (multi-tenancy root) ───────────────────────────
create table carriers (
    id         uuid primary key default gen_random_uuid(),
    name       text not null,
    created_at timestamptz default now()
);

-- Link Supabase auth users to carriers
create table carrier_members (
    id         uuid primary key default gen_random_uuid(),
    carrier_id uuid not null references carriers(id) on delete cascade,
    user_id    uuid not null references auth.users(id) on delete cascade,
    role       text not null default 'planner', -- 'admin' | 'planner' | 'viewer'
    created_at timestamptz default now(),
    unique (carrier_id, user_id)
);


-- ── PLANS ───────────────────────────────────────────────────
create table plans (
    id          uuid primary key default gen_random_uuid(),
    carrier_id  uuid not null references carriers(id) on delete cascade,
    filename    text not null,
    uploaded_at timestamptz default now()
);

create table tours (
    id               uuid primary key default gen_random_uuid(),
    plan_id          uuid not null references plans(id) on delete cascade,
    carrier_id       uuid not null references carriers(id) on delete cascade,
    external_tour_id text not null,  -- original tour_id from uploaded file
    created_at       timestamptz default now()
);

create table stops (
    id                 uuid primary key default gen_random_uuid(),
    tour_id            uuid not null references tours(id) on delete cascade,
    carrier_id         uuid not null references carriers(id) on delete cascade,
    sequence           int not null,
    location_name      text not null,
    planned_arrival    timestamptz,
    planned_departure  timestamptz,
    created_at         timestamptz default now()
);

create table legs (
    id           uuid primary key default gen_random_uuid(),
    tour_id      uuid not null references tours(id) on delete cascade,
    carrier_id   uuid not null references carriers(id) on delete cascade,
    from_stop_id uuid not null references stops(id),
    to_stop_id   uuid not null references stops(id),
    sequence     int not null,
    created_at   timestamptz default now()
);


-- ── EXECUTION ───────────────────────────────────────────────
create table execution_events (
    id                uuid primary key default gen_random_uuid(),
    carrier_id        uuid not null references carriers(id) on delete cascade,
    stop_id           uuid not null references stops(id) on delete cascade,
    actual_arrival    timestamptz,
    actual_departure  timestamptz,
    status            text not null default 'completed',  -- 'completed' | 'failed' | 'partial'
    failure_reason    text,
    source            text not null default 'csv_upload', -- 'csv_upload' | 'manual' | 'telematics'
    created_at        timestamptz default now()
);


-- ── GAPS (computed, stored for reporting & ML) ───────────────
create table stop_gaps (
    id                      uuid primary key default gen_random_uuid(),
    carrier_id              uuid not null references carriers(id) on delete cascade,
    stop_id                 uuid not null references stops(id) on delete cascade,
    execution_event_id      uuid not null references execution_events(id) on delete cascade,
    arrival_delta_minutes   int,   -- positive = late, negative = early, null = no planned time
    departure_delta_minutes int,
    is_failed               bool not null default false,
    computed_at             timestamptz default now()
);

create table tour_gaps (
    id                   uuid primary key default gen_random_uuid(),
    carrier_id           uuid not null references carriers(id) on delete cascade,
    tour_id              uuid not null references tours(id) on delete cascade,
    total_delay_minutes  int not null default 0,
    failed_stops         int not null default 0,
    total_stops          int not null default 0,
    computed_at          timestamptz default now()
);


-- ── INDEXES ─────────────────────────────────────────────────
create index on tours (plan_id);
create index on stops (tour_id);
create index on legs (tour_id);
create index on execution_events (stop_id);
create index on stop_gaps (stop_id);
create index on tour_gaps (tour_id);
create index on carrier_members (user_id);


-- ── ROW LEVEL SECURITY ──────────────────────────────────────
alter table carriers         enable row level security;
alter table carrier_members  enable row level security;
alter table plans            enable row level security;
alter table tours            enable row level security;
alter table stops            enable row level security;
alter table legs             enable row level security;
alter table execution_events enable row level security;
alter table stop_gaps        enable row level security;
alter table tour_gaps        enable row level security;

-- Helper: returns the carrier_id for the currently authenticated user
create or replace function get_my_carrier_id()
returns uuid
language sql stable
as $$
    select carrier_id
    from carrier_members
    where user_id = auth.uid()
    limit 1;
$$;

-- RLS policies — each user sees only their carrier's rows
create policy "carriers: members only"      on carriers         for all using (id          = get_my_carrier_id());
create policy "plans: carrier only"         on plans            for all using (carrier_id  = get_my_carrier_id());
create policy "tours: carrier only"         on tours            for all using (carrier_id  = get_my_carrier_id());
create policy "stops: carrier only"         on stops            for all using (carrier_id  = get_my_carrier_id());
create policy "legs: carrier only"          on legs             for all using (carrier_id  = get_my_carrier_id());
create policy "execution_events: carrier"   on execution_events for all using (carrier_id  = get_my_carrier_id());
create policy "stop_gaps: carrier only"     on stop_gaps        for all using (carrier_id  = get_my_carrier_id());
create policy "tour_gaps: carrier only"     on tour_gaps        for all using (carrier_id  = get_my_carrier_id());

-- carrier_members: users can see their own membership row
create policy "carrier_members: own rows"   on carrier_members  for all using (user_id = auth.uid());
