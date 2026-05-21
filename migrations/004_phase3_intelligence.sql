-- ============================================================
-- FREITIR — Phase 3: Intelligence
-- Run in: Supabase Dashboard → SQL Editor
-- ============================================================

-- Risk assessment per tour (one row per tour per plan upload)
create table tour_risks (
    id                        uuid primary key default gen_random_uuid(),
    carrier_id                uuid not null references carriers(id) on delete cascade,
    plan_id                   uuid not null references plans(id) on delete cascade,
    tour_id                   uuid not null references tours(id) on delete cascade,
    risk_score                decimal(5, 4) not null default 0,  -- 0.0 to 1.0
    risk_level                text not null default 'low',       -- 'low' | 'medium' | 'high'
    estimated_delay_minutes   int not null default 0,
    estimated_revenue_loss_eur decimal(10, 2) not null default 0,
    estimated_co2_kg          decimal(10, 4) not null default 0,
    flagged_stops             int not null default 0,
    computed_at               timestamptz default now()
);

-- Risk flag per stop within a tour risk (detail behind each tour_risk)
create table stop_risks (
    id                            uuid primary key default gen_random_uuid(),
    carrier_id                    uuid not null references carriers(id) on delete cascade,
    tour_risk_id                  uuid not null references tour_risks(id) on delete cascade,
    stop_id                       uuid not null references stops(id) on delete cascade,
    location_name                 text not null,
    risk_score                    decimal(5, 4) not null default 0,
    avg_historical_delay_minutes  decimal(10, 2),
    historical_failure_rate       decimal(5, 4),
    historical_sample_count       int not null default 0,
    recommended_action            text,
    computed_at                   timestamptz default now()
);

create index on tour_risks (plan_id);
create index on tour_risks (carrier_id);
create index on stop_risks (tour_risk_id);

-- RLS
alter table tour_risks enable row level security;
alter table stop_risks  enable row level security;

create policy "tour_risks: carrier only" on tour_risks
    for all using (carrier_id = get_my_carrier_id());

create policy "stop_risks: carrier only" on stop_risks
    for all using (carrier_id = get_my_carrier_id());
