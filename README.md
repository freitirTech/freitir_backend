# Freitir — Setup & Operating Guide

**Freitir** is an execution intelligence platform for road freight. It ingests transport plans, captures what actually happened (execution data), computes gaps between planned and actual performance, and generates risk scores and recommendations for future tours.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Prerequisites](#2-prerequisites)
3. [Project Structure](#3-project-structure)
4. [One-Time Setup](#4-one-time-setup)
   - [4.1 Supabase](#41-supabase)
   - [4.2 Backend](#42-backend)
   - [4.3 Frontend](#43-frontend)
5. [Database Migrations](#5-database-migrations)
6. [Environment Variables](#6-environment-variables)
7. [Starting the System](#7-starting-the-system)
8. [First-Time Use](#8-first-time-use)
9. [Daily Workflow](#9-daily-workflow)
10. [Sample Data](#10-sample-data)
11. [Simulator](#11-simulator)
12. [Data Formats](#12-data-formats)
13. [What Each Page Does](#13-what-each-page-does)
14. [Key Concepts](#14-key-concepts)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. System Overview

Freitir has three components:

| Component | Technology | Purpose |
|---|---|---|
| **Backend** | Python, FastAPI | API server — parses files, stores data, runs intelligence |
| **Frontend** | Next.js 16, React 19, Tailwind | Web UI |
| **Database** | Supabase (PostgreSQL) | Persistent storage, auth, row-level security |

### How data flows

```
Carrier uploads plan CSV  (with plan date)
        ↓
Backend parses → stores Plan / Tours / Stops / Legs
        ↓
Risk scored against historical patterns (instant)
        ↓
Carrier uploads execution CSV  —or—  runs Simulator
        ↓
Backend computes gaps (planned vs actual)
        ↓
Patterns refreshed (rolling 6-week memory per location)
        ↓
Plan re-scored with updated patterns
        ↓
Intelligence feed shows at-risk tours + recommendations
Performance page shows week-by-week trends
```

---

## 2. Prerequisites

Install these before starting:

| Tool | Version | Download |
|---|---|---|
| Python | 3.11 or later | https://python.org |
| Node.js | 18 or later | https://nodejs.org |
| Git | Any recent | https://git-scm.com |

Verify installations:

```bash
python --version     # should print 3.11+
node --version       # should print 18+
git --version
```

You also need a free **Supabase** account: https://supabase.com

---

## 3. Project Structure

```
freitir_backend/
├── app/
│   ├── api/              # Route handlers (plans, execution, analytics, simulator, etc.)
│   ├── core/             # Auth, config, Supabase client
│   ├── schemas/          # Pydantic models
│   └── services/         # Business logic
├── migrations/           # SQL files to run in Supabase (run in order)
├── sample_data/          # 6 weeks of realistic test data (see Section 10)
├── .env                  # Secret keys (not committed to git)
└── requirements.txt
```

---

## 4. One-Time Setup

### 4.1 Supabase

**Create the project:**

1. Go to https://supabase.com and sign in
2. Click **New project**
3. Name it `freitir`, choose a region close to you, set a database password
4. Wait 1–2 minutes for the project to spin up

**Get your credentials:**

Go to **Settings → API**. You need three values:

| Value | Where to find it | Used in |
|---|---|---|
| Project URL | Top of Settings → API | Both `.env` files |
| `anon` public key | Under "Project API Keys" | Both `.env` files |
| `service_role` secret key | Under "Project API Keys" (click reveal) | Backend `.env` only |

> ⚠️ The `service_role` key bypasses all security. Never commit it to git or share it publicly.

**Disable email confirmation (for development):**

Go to **Authentication → Providers → Email** and turn off **"Confirm email"**.

---

### 4.2 Backend

```bash
cd freitir_backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac/Linux

# Install dependencies
pip install -r requirements.txt
pip install supabase
```

---

### 4.3 Frontend

```bash
cd freitir_frontend
npm install
```

---

## 5. Database Migrations

Migrations must be run **in order**, **once each**, in Supabase → SQL Editor → New query.

### Migration 001 — Initial schema

**File:** `migrations/001_initial_schema.sql`

Creates: `carriers`, `carrier_members`, `plans`, `tours`, `stops`, `legs`, `execution_events`, `stop_gaps`, `tour_gaps`

---

### Migration 002 — Dev carrier seed

**File:** `migrations/002_seed_dev_carrier.sql`

Creates one dev carrier row for local development.

---

### Migration 003 — Phase 2: Memory

**File:** `migrations/003_phase2_memory.sql`

Creates: `carrier_settings`, `patterns`

---

### Migration 004 — Phase 3: Intelligence

**File:** `migrations/004_phase3_intelligence.sql`

Creates: `tour_risks`, `stop_risks`

---

### Migration 005 — Plan date

**File:** `migrations/005_add_plan_date.sql`

Adds `plan_date DATE` column to `plans` and an index for time-series queries.

If you can't open the file directly, paste this into the SQL editor:

```sql
ALTER TABLE plans ADD COLUMN IF NOT EXISTS plan_date DATE;
CREATE INDEX IF NOT EXISTS idx_plans_carrier_date ON plans(carrier_id, plan_date);
```

---

**Verify:** Go to Supabase → Table Editor. You should see all of these tables:

`carriers` · `carrier_members` · `plans` · `tours` · `stops` · `legs` · `execution_events` · `stop_gaps` · `tour_gaps` · `carrier_settings` · `patterns` · `tour_risks` · `stop_risks`

---

## 6. Environment Variables

### Backend: `freitir_backend/.env`

Create this file (gitignored — never commit it):

```
DATABASE_URL=
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
ORS_API_KEY=
```

### Frontend: `freitir_frontend/.env.local`

Create this file (gitignored — never commit it):

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> Only the anon key goes in the frontend — never the service_role key.

---

## 7. Starting the System

Always start the **backend first**, then the frontend.

### Terminal 1 — Backend

```bash
cd freitir_backend
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac/Linux
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Verify: http://localhost:8000/health → `{"status": "ok"}`

### Terminal 2 — Frontend

```bash
cd freitir_frontend
npm run dev
```

Open: http://localhost:3000

You will be redirected to `/auth`. This is correct.

> Always use http://localhost:3000 directly in your browser — not the Claude Code preview — so the file picker works properly when uploading CSVs.

---

## 8. First-Time Use

### Step 1: Create an account

1. Go to http://localhost:3000 → redirected to `/auth`
2. Click **"Create account"**, enter email + password (min 6 chars), submit
3. Switch to **"Sign in"** and sign in

### Step 2: Set up your company

You will be redirected to `/onboard`. Enter your company name and click **"Get started"**.

---

## 9. Daily Workflow

### Upload a transport plan

1. From the home page, click **"Upload Plan"**
2. A modal opens — set the **plan date** (the date the tours will actually run, not today's date if you're uploading in advance). Defaults to today.
3. Choose your `.csv` or `.xlsx` file — it uploads immediately

> The plan date is used for week-by-week trend analysis on the Performance page. Always set it correctly.

### Upload execution data

1. Click on a plan in the list to open it
2. Click **"Upload Execution"** → select the execution `.csv`

### Run a simulation (no CSV needed)

1. Open any plan
2. Click **"Simulate"** → pick a scenario:
   - **On time** — minor variation, good for seeding baseline data
   - **Delayed** — 20–45 min cascading delays
   - **Disrupted** — random stop failures + moderate delays
3. Gaps, patterns, and risk scores update automatically

---

## 10. Sample Data

`sample_data/` contains 6 weeks of realistic test data — 3 tours per week, same routes, encoded performance patterns.

**Routes:**
- **T001**: Hamburg → Bremen → Hannover
- **T002**: Berlin → Leipzig → Dresden
- **T003**: Frankfurt → Stuttgart → Munich

**Encoded patterns** (what the intelligence will learn after all 6 weeks):

| Location | Pattern | Expected risk |
|---|---|---|
| Frankfurt | +28–45 min every week (traffic) | High |
| Berlin | Fails 3 out of 6 weeks (access denied) | High |
| Bremen | +12–25 min every week (loading dock) | Medium |
| Stuttgart / Munich | Cascade delay from Frankfurt | Medium |
| Hamburg / Leipzig / Dresden | Mostly on time | Low |

**How to load 6 weeks of memory:**

Upload each pair in order — plan first, then execution. Set the plan date to match the filename.

| Plan file | Plan date | Execution file |
|---|---|---|
| `plan_week1.csv` | 2026-04-07 | `execution_week1.csv` |
| `plan_week2.csv` | 2026-04-14 | `execution_week2.csv` |
| `plan_week3.csv` | 2026-04-21 | `execution_week3.csv` |
| `plan_week4.csv` | 2026-04-28 | `execution_week4.csv` |
| `plan_week5.csv` | 2026-05-05 | `execution_week5.csv` |
| `plan_week6.csv` | 2026-05-12 | `execution_week6.csv` |

After all 6 weeks: check Intelligence (Frankfurt and Berlin high risk) and Performance → Week by week (6 rows of trend data).

**To reset and start clean:**

In Supabase → SQL Editor:
```sql
DELETE FROM plans;
DELETE FROM patterns;
```
This cascades through all child tables.

---

## 11. Simulator

The simulator generates synthetic TMS events based on Samsara's RouteStop event schema — no CSV needed.

**API:** `POST /simulator/run`

```json
{ "plan_id": "uuid", "scenario": "on_time" }
```

Scenarios: `on_time` · `delayed` · `disrupted`

**UI:** Open any plan → click **"Simulate"** → pick a scenario.

Each run flows through the full pipeline: execution events → gaps → patterns → risk scores. The Intelligence feed and Performance page update immediately.

Use the simulator to:
- Quickly build up memory without preparing CSV files
- Demo the product to a customer whose data isn't loaded yet
- Test how the intelligence responds to different operational conditions

---

## 12. Data Formats

### Plan CSV

```csv
tour_id,stop_sequence,location,planned_arrival,planned_departure
T001,1,Hamburg,2026-04-07 07:00,2026-04-07 07:30
T001,2,Bremen,2026-04-07 09:15,2026-04-07 10:00
T001,3,Hannover,2026-04-07 12:00,2026-04-07 12:30
```

| Column | Required | Description |
|---|---|---|
| `tour_id` | ✓ | Identifier for the tour (e.g. T001) |
| `stop_sequence` | ✓ | Order of stop within the tour (1, 2, 3…) |
| `location` | ✓ | Name of the stop location |
| `planned_arrival` | Optional | Format: `YYYY-MM-DD HH:MM` |
| `planned_departure` | Optional | Format: `YYYY-MM-DD HH:MM` |

### Execution CSV

```csv
tour_id,stop_sequence,actual_arrival,actual_departure,status,failure_reason
T001,1,2026-04-07 07:05,2026-04-07 07:35,completed,
T001,2,2026-04-07 09:33,2026-04-07 10:20,completed,
T001,3,2026-04-07 13:30,,failed,customer not available
```

| Column | Required | Description |
|---|---|---|
| `tour_id` | ✓ | Must match the plan exactly |
| `stop_sequence` | ✓ | Must match the plan exactly |
| `actual_arrival` | Optional | Leave blank if stop failed before arrival |
| `actual_departure` | Optional | Leave blank if truck didn't depart |
| `status` | Optional | `completed` (default), `failed`, or `partial` |
| `failure_reason` | Optional | Free text |

---

## 13. What Each Page Does

### `/` — Plans list

All uploaded plans. Each shows filename, plan date, tour count, and whether execution data has been uploaded (green) or not (amber).

### `/plans/[id]` — Plan detail

Full structure of one plan: tours → stops → gap deltas. Green = early, red = late. Also shows **Simulate** and **Upload Execution** buttons.

### `/intelligence` — Intelligence feed

All tours scored against historical patterns, ranked high → medium → low risk.

- **High** (≥ 0.5) — needs attention before dispatch
- **Medium** (0.2–0.5) — worth monitoring
- **Low** (< 0.2) — on track

Expand any tour to see stop-level breakdown with recommended actions. Becomes meaningful after 2–3 weeks of execution history.

### `/analytics` — Performance

Rolling 6-week view:
- **Week by week table** — one row per plan date: delay, failed stops, revenue lost
- **Worst locations** — top 5 by average arrival delay
- **All location patterns** — full table ranked by avg delay

Revenue lost = delay minutes × €80/hr · CO₂ = delay minutes × 2.5 kg/hr

### `/auth` — Sign in / Sign up

### `/onboard` — Company setup (one time)

---

## 14. Key Concepts

**Tour** — A single truck's route for a day: an ordered sequence of stops.

**Stop** — One delivery or collection point, with planned arrival and departure times.

**Gap** — Difference between planned and actual time at a stop, in minutes. Positive = late, negative = early.

**Plan date** — The date the tours actually run. Set this correctly at upload time — it drives the week-by-week trend analysis.

**Pattern** — Rolling 6-week aggregate per location: average delay, failure rate, sample count. This is Freitir's institutional memory.

**Risk score** — 0.0–1.0 per stop, based on historical delay and failure rate. Rolls up to tour level. Recomputed every time execution data is uploaded.

**Simulator** — Generates synthetic execution events (based on Samsara RouteStop schema) for a plan, running the full pipeline without a CSV. Three scenarios: on time, delayed, disrupted.

**Revenue lost** — Delay minutes × €80/hr (all-in HGV cost including driver and depreciation).

**CO₂ from idle** — Delay minutes × 2.5 kg/hr (diesel HGV idle burn estimate).

---

## 15. Troubleshooting

### "Could not load plans" / "Could not load analytics"

Backend not running, or JWT expired.

1. Check uvicorn is running: http://localhost:8000/health → `{"status":"ok"}`
2. Check `freitir_backend/.env` for typos
3. Sign out and sign back in to refresh the token

---

### "Failed to create canonical plan: Could not find the table..."

A migration hasn't been run. The error names the missing table — find it in Section 5 and run its migration.

---

### "Failed to process execution data: invalid input syntax for type timestamp"

A date/time value in your CSV couldn't be parsed. Use format `YYYY-MM-DD HH:MM`. Leave empty cells blank — not "N/A" or "-".

---

### "Onboarding incomplete" when uploading

Go to http://localhost:3000/onboard and complete the company setup.

---

### Intelligence shows all "low risk" after uploading a plan

Plans are scored at upload time. If no patterns exist yet, all scores are zero. Upload execution data (or run the Simulator) — patterns will build and the plan re-scores automatically.

---

### File picker doesn't work / "outside session folder" error

Use http://localhost:3000 directly in your browser (Chrome/Edge/Firefox), not the Claude Code built-in preview. The preview sandboxes file access.

---

### The same plan appears multiple times

Each upload creates a new record. To reset:

```sql
DELETE FROM plans;
DELETE FROM patterns;
```

---

### Backend crashes on startup with "SUPABASE_URL not set"

Create `freitir_backend/.env` with the values from Section 6. No spaces around `=`.

---

*Last updated: May 2026*
