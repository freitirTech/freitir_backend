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
10. [Data Formats](#10-data-formats)
11. [What Each Page Does](#11-what-each-page-does)
12. [Key Concepts](#12-key-concepts)
13. [Troubleshooting](#13-troubleshooting)

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
Carrier uploads plan CSV
        ↓
Backend parses → stores Plan / Tours / Stops / Legs
        ↓
Risk scored against historical patterns (instant)
        ↓
Carrier uploads execution CSV (actual times per stop)
        ↓
Backend computes gaps (planned vs actual)
        ↓
Patterns refreshed (rolling 6-week memory)
        ↓
Plan re-scored with updated patterns
        ↓
Intelligence feed shows at-risk tours + recommendations
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
freitir/
├── freitir_backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/              # Route handlers (plans, execution, analytics, etc.)
│   │   ├── core/             # Auth, config, Supabase client
│   │   ├── schemas/          # Pydantic models
│   │   └── services/         # Business logic
│   ├── migrations/           # SQL files to run in Supabase
│   ├── .env                  # Secret keys (not committed to git)
│   └── requirements.txt
│
├── freitir_frontend/         # Next.js frontend
│   ├── app/                  # Pages (auth, plans, intelligence, analytics)
│   ├── lib/                  # API client, Supabase browser/server clients
│   ├── proxy.ts              # Route protection (auth guard)
│   └── .env.local            # Secret keys (not committed to git)
│
├── sample_plan.csv           # Example transport plan for testing
├── sample_execution.csv      # Example execution data for testing
└── SETUP.md                  # This file
```

---

## 4. One-Time Setup

### 4.1 Supabase

**Create the project:**

1. Go to https://supabase.com and sign in
2. Click **New project**
3. Name it `freitir`, choose a region close to you, set a database password
4. Wait 1–2 minutes for the project to spin up (the dashboard will show "Project is ready")

**Get your credentials:**

Go to **Settings → API**. You need three values:

| Value | Where to find it | Used in |
|---|---|---|
| Project URL | Top of Settings → API | Both `.env` files |
| `anon` public key | Under "Project API Keys" | Both `.env` files |
| `service_role` secret key | Under "Project API Keys" (click reveal) | Backend `.env` only |

> ⚠️ The `service_role` key bypasses all security. Never commit it to git or share it publicly.

**Disable email confirmation (for development):**

Go to **Authentication → Providers → Email** and turn off **"Confirm email"**. This lets you create test accounts without clicking confirmation links.

---

### 4.2 Backend

Open a terminal and run:

```bash
cd freitir_backend

# Create a virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install supabase
```

**Expected output:** A long list of packages installing. No errors.

---

### 4.3 Frontend

Open a second terminal and run:

```bash
cd freitir_frontend
npm install
```

**Expected output:** Packages installing. You may see audit warnings — these are safe to ignore for development.

---

## 5. Database Migrations

Migrations must be run **in order** and **only once each**. They create all the tables Freitir needs.

Go to your Supabase project → **SQL Editor** → **New query**. For each file below, paste the full contents and click **Run**.

### Migration 001 — Initial schema

**File:** `freitir_backend/migrations/001_initial_schema.sql`

**Creates:** `carriers`, `carrier_members`, `plans`, `tours`, `stops`, `legs`, `execution_events`, `stop_gaps`, `tour_gaps`

**Expected result:** "Success. No rows returned."

---

### Migration 002 — Dev carrier seed

**File:** `freitir_backend/migrations/002_seed_dev_carrier.sql`

**Creates:** One carrier row with a known ID for development use before auth is wired.

**Expected result:** "Success. No rows returned."

> This is only needed for development. In production, carriers are created through the onboarding flow.

---

### Migration 003 — Phase 2: Memory

**File:** `freitir_backend/migrations/003_phase2_memory.sql`

**Creates:** `carrier_settings`, `patterns`

**Expected result:** "Success. No rows returned."

---

### Migration 004 — Phase 3: Intelligence

**File:** `freitir_backend/migrations/004_phase3_intelligence.sql`

**Creates:** `tour_risks`, `stop_risks`

**Expected result:** "Success. No rows returned."

---

**Verify migrations ran correctly:**

Go to **Table Editor** in Supabase. You should see these tables listed:

`carriers` · `carrier_members` · `plans` · `tours` · `stops` · `legs` · `execution_events` · `stop_gaps` · `tour_gaps` · `carrier_settings` · `patterns` · `tour_risks` · `stop_risks`

If any table is missing, re-run its migration.

---

## 6. Environment Variables

### Backend: `freitir_backend/.env`

Create this file (it is gitignored — never commit it):

```
DATABASE_URL=
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
ORS_API_KEY=
```

Replace the values with your credentials from Supabase → Settings → API.

---

### Frontend: `freitir_frontend/.env.local`

Create this file (it is gitignored — never commit it):

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> `NEXT_PUBLIC_` prefix means the value is exposed to the browser — only put the anon key here, never the service role key.

---

## 7. Starting the System

You need **two terminals running simultaneously**.

### Terminal 1 — Backend

```bash
cd freitir_backend

# Activate virtual environment first
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac/Linux

# Start the server
uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Verify it works:** Open http://localhost:8000/health in your browser. You should see:
```json
{"status": "ok"}
```

If you see an error here, check your `.env` file — a missing or wrong `SUPABASE_URL` is the most common cause.

---

### Terminal 2 — Frontend

```bash
cd freitir_frontend
npm run dev
```

**Expected output:**
```
▲ Next.js 16.x.x
- Local: http://localhost:3000
```

**Open the app:** http://localhost:3000

You will be redirected to `/auth` (the login page). This is correct — the app requires authentication.

---

### Startup sequence

Always start the **backend first**, then the frontend. The frontend makes API calls to the backend on every page load — if the backend isn't running, pages will show "Could not load" errors.

---

## 8. First-Time Use

### Step 1: Create an account

1. Go to http://localhost:3000 — you will be redirected to `/auth`
2. Click **"Create account"**
3. Enter your email and a password (minimum 6 characters)
4. Click **"Create account"**
5. Switch to **"Sign in"** tab and sign in with the same credentials

### Step 2: Set up your company

After signing in, you will be redirected to `/onboard`.

1. Enter your company name (e.g. "Acme Logistics")
2. Click **"Get started"**

You will land on the plans list (home page). This is your dashboard.

> If you skip this step or something goes wrong, go to http://localhost:3000/onboard manually.

---

## 9. Daily Workflow

### Upload a transport plan

A transport plan is a CSV or Excel file describing tomorrow's deliveries.

1. From the home page, click **"Upload Plan"** (top right)
2. Select a `.csv` or `.xlsx` file
3. The plan appears in the list immediately

**What happens behind the scenes:**
- The file is parsed into Tours → Stops → Legs
- Each stop is risk-scored against historical patterns
- If this is your first plan ever, all tours will show as "low risk" (no historical data yet)

**Required CSV columns:** `tour_id`, `stop_sequence`, `location`

**Optional CSV columns:** `planned_arrival`, `planned_departure`

---

### Upload execution data

After tours have run, upload what actually happened.

1. Click on a plan in the list to open it
2. Click **"Upload Execution"** (top right of the plan detail page)
3. Select the execution `.csv` file

**What happens behind the scenes:**
- Each row is matched to its planned stop by `tour_id` + `stop_sequence`
- Gaps are computed: `actual_arrival − planned_arrival` in minutes
- Location patterns are refreshed (rolling 6-week memory)
- The plan's risk scores are recomputed with the updated patterns

**Required CSV columns:** `tour_id`, `stop_sequence`

**Optional CSV columns:** `actual_arrival`, `actual_departure`, `status`, `failure_reason`

Valid values for `status`: `completed`, `failed`, `partial`

---

### Read the Intelligence feed

Click **"Intelligence"** from the home page.

Tours are ranked by risk level: **High → Medium → Low**.

For each tour you see:
- Estimated delay in minutes
- Revenue at risk in euros
- CO₂ from idle time in kg
- Number of flagged stops

Click **"Details"** on any tour to see stop-level breakdown with a specific recommended action for each flagged stop.

> The intelligence feed only becomes meaningful after you have uploaded execution data for several plans. With one plan's worth of data, patterns are based on a single run — scores will update and stabilise as more execution data comes in.

---

### Read the Performance page

Click **"Performance"** from the home page.

This shows a rolling 6-week view:
- Total revenue lost to delays
- Total CO₂ from idle time
- Failed stop count
- Location patterns table — which stops are consistently late or failing

---

## 10. Data Formats

### Plan CSV

```csv
tour_id,stop_sequence,location,planned_arrival,planned_departure
T001,1,Hamburg,2026-04-02 08:00,2026-04-02 08:30
T001,2,Bremen,2026-04-02 10:15,2026-04-02 11:00
T001,3,Hannover,2026-04-02 13:00,2026-04-02 13:30
T002,1,Berlin,2026-04-02 07:30,2026-04-02 08:00
T002,2,Leipzig,2026-04-02 10:30,2026-04-02 11:15
```

| Column | Required | Description |
|---|---|---|
| `tour_id` | ✓ | Identifier for the tour (e.g. T001, route-A) |
| `stop_sequence` | ✓ | Order of stop within the tour (1, 2, 3…) |
| `location` | ✓ | Name of the stop location |
| `planned_arrival` | Optional | Format: `YYYY-MM-DD HH:MM` |
| `planned_departure` | Optional | Format: `YYYY-MM-DD HH:MM` |

---

### Execution CSV

```csv
tour_id,stop_sequence,actual_arrival,actual_departure,status,failure_reason
T001,1,2026-04-02 08:05,2026-04-02 08:35,completed,
T001,2,2026-04-02 10:45,2026-04-02 11:20,completed,
T001,3,2026-04-02 13:30,,failed,customer not available
T002,1,2026-04-02 07:25,2026-04-02 08:05,completed,
T002,2,2026-04-02 10:15,2026-04-02 11:00,completed,
```

| Column | Required | Description |
|---|---|---|
| `tour_id` | ✓ | Must match a tour_id in the uploaded plan |
| `stop_sequence` | ✓ | Must match the sequence in the plan |
| `actual_arrival` | Optional | Leave empty if stop failed before arrival |
| `actual_departure` | Optional | Leave empty if truck didn't depart |
| `status` | Optional | `completed` (default), `failed`, or `partial` |
| `failure_reason` | Optional | Free text description of why a stop failed |

> The `tour_id` and `stop_sequence` must exactly match the values in the plan CSV — this is how the system links execution data back to planned stops.

---

## 11. What Each Page Does

### `/` — Plans list

Shows all uploaded transport plans for your carrier. Each plan shows:
- Filename and upload date
- Number of tours
- Whether execution data has been uploaded (green badge) or not (amber badge)

Click a plan to open it.

---

### `/plans/[id]` — Plan detail

Shows the full structure of one plan: each tour, its stops, and (if execution has been uploaded) the delay deltas per stop.

- **Green numbers** = arrived/departed early
- **Red numbers** = arrived/departed late
- **"Failed" badge** = stop was marked as failed in execution data

Also shows the "Upload Execution" button for this specific plan.

---

### `/intelligence` — Intelligence feed

Shows all tours scored against historical patterns, ranked by risk level.

- **High risk (red)** = risk score ≥ 0.5 — needs attention before dispatch
- **Medium risk (amber)** = risk score 0.2–0.5 — worth monitoring
- **Low risk (green)** = risk score < 0.2 — on track

Each tour shows estimated delay, revenue at risk, CO₂ impact, and a specific recommended action per flagged stop.

The feed is most useful when you have at least 2–3 weeks of execution history, so patterns are based on multiple runs rather than a single data point.

---

### `/analytics` — Performance

Rolling 6-week summary:
- **Revenue lost** = total delay minutes × €80/hr (default rate)
- **CO₂ from idle** = total delay minutes × 2.5kg/hr (diesel HGV estimate)
- **Worst locations** = stops ranked by average arrival delay

The location patterns table is the core of Freitir's memory — it shows which depots and delivery points are consistently problematic.

---

### `/auth` — Sign in / Sign up

Standard email + password authentication via Supabase Auth.

---

### `/onboard` — Company setup

One-time step after account creation. Sets your carrier name in the system. All your plans, patterns, and intelligence are isolated to your carrier account.

---

## 12. Key Concepts

**Tour** — A single truck's route for a day: an ordered sequence of stops.

**Stop** — One delivery or collection point on a tour, with planned arrival and departure times.

**Leg** — The road segment between two consecutive stops.

**Gap** — The difference between what was planned and what actually happened at a stop. Measured in minutes (positive = late, negative = early).

**Pattern** — A rolling 6-week aggregate per location: average delay, failure rate, number of runs. This is Freitir's "institutional memory."

**Risk score** — A number from 0.0 to 1.0 assigned to each stop based on its historical pattern. Rolls up to a tour-level score. Scored every time a plan is uploaded.

**Revenue lost** — Delay minutes converted to euros using a €80/hour truck cost. This is the default all-in cost for a heavy goods vehicle including driver time and vehicle depreciation.

**CO₂ from idle** — Delay minutes converted to kilograms of CO₂ using 2.5kg/hour idle burn rate for a diesel HGV. This is an estimate — accuracy improves when telematics distance data is available.

---

## 13. Troubleshooting

### "Could not load plans" / "Could not load analytics"

**Cause:** Backend is not running, or the JWT token has expired.

**Fix:**
1. Make sure uvicorn is running (Terminal 1)
2. Check http://localhost:8000/health — it should return `{"status":"ok"}`
3. If it returns an error, check your `freitir_backend/.env` file for typos
4. Try signing out and signing back in to refresh the token

---

### "Failed to create canonical plan: Could not find the table..."

**Cause:** A database migration hasn't been run yet.

**Fix:** Go to Supabase → SQL Editor and run the missing migration file. The error message names the missing table — find the migration that creates it in the list in Section 5.

---

### "Failed to process execution data: invalid input syntax for type timestamp"

**Cause:** A date/time value in your execution CSV couldn't be parsed.

**Fix:** Make sure all date columns use the format `YYYY-MM-DD HH:MM`. Empty cells are fine — leave them blank, not "N/A" or "-".

---

### "Onboarding incomplete" error when uploading

**Cause:** The account was created but the company name step was skipped.

**Fix:** Go to http://localhost:3000/onboard and complete the company setup.

---

### Intelligence shows all "low risk" after uploading a plan

**Cause:** Plans are scored at upload time. If you upload the plan before uploading any execution data, there are no patterns yet, so all scores are zero (low risk).

**Fix:** Upload execution data for the plan. This builds the patterns and automatically re-scores the plan. The Intelligence feed will update.

---

### The same plan appears multiple times in the list

**Cause:** The plan was uploaded more than once (each upload creates a new record).

**Fix:** In Supabase → SQL Editor, run:
```sql
delete from plans;
delete from patterns;
```
This cascades through all related data. Then do a clean upload.

---

### Backend crashes on startup with "SUPABASE_URL not set"

**Cause:** The `.env` file is missing or empty.

**Fix:** Create `freitir_backend/.env` with the values from Section 6. Make sure there are no spaces around the `=` sign.

---

*Last updated: May 2026*
