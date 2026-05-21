"""
TMS / Telematics Simulator

Generates realistic synthetic execution events for a plan without needing a CSV.
Models three real-world scenarios based on Samsara RouteStop event patterns.

Scenario behaviour:
  on_time   — minor variation ±5 min, virtually no cascade, 0% failure
  delayed   — 20–45 min base delay, strong cascade (delays stack), 5% failure
  disrupted — random 1–2 stops fail, failures cascade to downstream stops, 10–25 min base delay
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.supabase_client import get_supabase
from app.schemas.execution import ExecutionEventIn, ExecutionUploadResult
from app.services.execution_db_service import save_execution

# Scenario parameters
SCENARIOS: dict[str, dict[str, Any]] = {
    "on_time": {
        "label": "On time",
        "base_delay_min": -5,
        "base_delay_max": 10,
        "cascade_factor": 0.15,   # delay mostly recovers between stops
        "failure_probability": 0.0,
        "failure_reasons": [],
    },
    "delayed": {
        "label": "Delayed",
        "base_delay_min": 20,
        "base_delay_max": 45,
        "cascade_factor": 0.75,   # delays stack heavily across the tour
        "failure_probability": 0.05,
        "failure_reasons": ["customer not available", "loading dock occupied"],
    },
    "disrupted": {
        "label": "Disrupted",
        "base_delay_min": 10,
        "base_delay_max": 30,
        "cascade_factor": 0.55,
        "failure_probability": 0.20,
        "failure_reasons": [
            "customer not available",
            "address not found",
            "access denied",
            "goods refused",
            "time window expired",
        ],
    },
}


def run_simulation(
    plan_id: str,
    carrier_id: str,
    scenario: str,
) -> ExecutionUploadResult | None:
    """
    Load the plan's stops, generate synthetic actual times per the chosen scenario,
    then pipe the events through the standard save_execution pipeline so gaps,
    patterns, and risk scores are all updated exactly as they would be with real data.
    """
    params = SCENARIOS[scenario]
    db = get_supabase()

    tours = (
        db.table("tours")
        .select("id, external_tour_id")
        .eq("plan_id", plan_id)
        .eq("carrier_id", carrier_id)
        .execute()
    ).data

    if not tours:
        return None

    tour_id_map: dict[str, str] = {t["id"]: t["external_tour_id"] for t in tours}
    tour_ids = list(tour_id_map.keys())

    stops = (
        db.table("stops")
        .select("id, tour_id, sequence, planned_arrival, planned_departure")
        .in_("tour_id", tour_ids)
        .order("sequence")
        .execute()
    ).data

    # Group stops by tour
    stops_by_tour: dict[str, list[dict]] = {}
    for stop in stops:
        stops_by_tour.setdefault(stop["tour_id"], []).append(stop)

    events: list[ExecutionEventIn] = []

    for db_tour_id, tour_stops in stops_by_tour.items():
        external_tour_id = tour_id_map[db_tour_id]
        cumulative_delay = 0.0

        for stop in sorted(tour_stops, key=lambda s: s["sequence"]):
            # Each stop picks a fresh base delta and accumulates the cascade from upstream
            base = random.uniform(params["base_delay_min"], params["base_delay_max"])
            cumulative_delay = cumulative_delay * params["cascade_factor"] + base
            delay = cumulative_delay

            is_failed = random.random() < params["failure_probability"]

            if is_failed:
                # Failed stops: driver arrived but couldn't complete; no departure
                actual_arrival = _shift(stop["planned_arrival"], delay)
                actual_departure = None
                status = "failed"
                failure_reason = random.choice(params["failure_reasons"])
                # A failure adds extra time lost at this stop — cascades harder downstream
                cumulative_delay += random.uniform(15, 30)
            else:
                actual_arrival = _shift(stop["planned_arrival"], delay)
                # Service time variation: driver may be faster or slower than planned
                dep_extra = random.uniform(-5, 10)
                actual_departure = _shift(stop["planned_departure"], delay + dep_extra)
                status = "completed"
                failure_reason = None

            events.append(ExecutionEventIn(
                tour_id=external_tour_id,
                stop_sequence=stop["sequence"],
                actual_arrival=actual_arrival,
                actual_departure=actual_departure,
                status=status,
                failure_reason=failure_reason,
            ))

    result = save_execution(plan_id=plan_id, carrier_id=carrier_id, events=events)

    return SimulatorRunResult_from(result, scenario, len(events))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _shift(planned_time_str: str | None, delta_minutes: float) -> str | None:
    """Parse a planned timestamp, shift it by delta_minutes, return ISO string."""
    if not planned_time_str:
        return None
    try:
        dt = datetime.fromisoformat(str(planned_time_str))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return (dt + timedelta(minutes=delta_minutes)).isoformat()
    except ValueError:
        return None


def SimulatorRunResult_from(
    upload_result: ExecutionUploadResult,
    scenario: str,
    events_generated: int,
) -> "SimulatorRunResult":
    from app.schemas.simulator import SimulatorRunResult
    return SimulatorRunResult(
        plan_id=upload_result.plan_id,
        scenario=scenario,
        events_generated=events_generated,
        stop_gaps_computed=upload_result.stop_gaps_computed,
        tour_gaps_computed=upload_result.tour_gaps_computed,
    )
