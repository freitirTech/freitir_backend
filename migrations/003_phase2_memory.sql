-- ============================================================
-- FREITIR — Phase 2: Memory
-- Run in: Supabase Dashboard → SQL Editor
-- ============================================================

-- Rate card and CO₂ factor per carrier (one row per carrier)
create table carrier_settings (
    id              uuid primary key default gen_random_uuid(),
    carrier_id      uuid not null references carriers(id) on delete cascade,
    hourly_rate_eur decimal(10, 2) not null default 80.00,
    co2_kg_per_idle_hour decimal(10, 4) not null default 2.5,
    updated_at      timestamptz default now(),
    unique (carrier_id)
);

-- Rolling 6-week patterns per location (one row per carrier + location)
create table patterns (
    id                       uuid primary key default gen_random_uuid(),
    carrier_id               uuid not null references carriers(id) on delete cascade,
    location_name            text not null,
    sample_count             int not null default 0,
    avg_arrival_delta_minutes decimal(10, 2),
    failure_rate             decimal(5, 4),   -- 0.0000 to 1.0000
    computed_at              timestamptz default now(),
    unique (carrier_id, location_name)
);

create index on patterns (carrier_id);

-- RLS
alter table carrier_settings enable row level security;
alter table patterns          enable row level security;

create policy "carrier_settings: carrier only" on carrier_settings
    for all using (carrier_id = get_my_carrier_id());

create policy "patterns: carrier only" on patterns
    for all using (carrier_id = get_my_carrier_id());
