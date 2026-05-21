-- Migration 005: Add plan_date to plans table
-- plan_date = the actual date the tours ran (not when the file was uploaded)
-- Enables time-series analytics: week-by-week performance trends

ALTER TABLE plans ADD COLUMN IF NOT EXISTS plan_date DATE;

-- Index for time-series queries grouped by carrier + date
CREATE INDEX IF NOT EXISTS idx_plans_carrier_date ON plans(carrier_id, plan_date);
