from app.core.supabase_client import get_supabase
from app.schemas.execution import ExecutionEventIn, ExecutionUploadResult
from app.services.gap_analysis_service import compute_stop_gaps, compute_tour_gaps
from app.services.memory_service import compute_patterns
from app.services.risk_scoring_service import score_plan


def save_execution(
    plan_id: str,
    carrier_id: str,
    events: list[ExecutionEventIn],
) -> ExecutionUploadResult:
    db = get_supabase()

    # Load all stops for this plan in one query, keyed by (external_tour_id, sequence)
    stops_result = (
        db.table("stops")
        .select("id, sequence, planned_arrival, planned_departure, tour_id")
        .eq("carrier_id", carrier_id)
        .execute()
    )

    tours_result = (
        db.table("tours")
        .select("id, external_tour_id")
        .eq("plan_id", plan_id)
        .eq("carrier_id", carrier_id)
        .execute()
    )

    tour_id_map: dict[str, str] = {
        t["external_tour_id"]: t["id"] for t in tours_result.data
    }

    # {(external_tour_id, sequence): stop row}
    stop_lookup: dict[tuple[str, int], dict] = {}
    for stop in stops_result.data:
        db_tour_id = stop["tour_id"]
        ext_tour_id = next(
            (ext for ext, db_id in tour_id_map.items() if db_id == db_tour_id), None
        )
        if ext_tour_id:
            stop_lookup[(ext_tour_id, stop["sequence"])] = stop

    events_saved = 0
    stop_gaps_computed = 0
    touched_tour_ids: set[str] = set()

    for event in events:
        key = (event.tour_id, event.stop_sequence)
        stop = stop_lookup.get(key)
        if stop is None:
            continue

        result = db.table("execution_events").insert({
            "carrier_id": carrier_id,
            "stop_id": stop["id"],
            "actual_arrival": event.actual_arrival,
            "actual_departure": event.actual_departure,
            "status": event.status,
            "failure_reason": event.failure_reason,
            "source": "csv_upload",
        }).execute()

        execution_event_id: str = result.data[0]["id"]
        events_saved += 1

        compute_stop_gaps(
            db=db,
            carrier_id=carrier_id,
            execution_event_id=execution_event_id,
            stop_id=stop["id"],
            actual_arrival=event.actual_arrival,
            actual_departure=event.actual_departure,
            planned_arrival=stop["planned_arrival"],
            planned_departure=stop["planned_departure"],
            is_failed=event.status == "failed",
        )
        stop_gaps_computed += 1
        touched_tour_ids.add(stop["tour_id"])

    for db_tour_id in touched_tour_ids:
        compute_tour_gaps(db=db, carrier_id=carrier_id, tour_id=db_tour_id)

    # Refresh patterns, then re-score the plan with updated patterns
    compute_patterns(carrier_id=carrier_id)
    score_plan(plan_id=plan_id, carrier_id=carrier_id)

    return ExecutionUploadResult(
        plan_id=plan_id,
        events_saved=events_saved,
        stop_gaps_computed=stop_gaps_computed,
        tour_gaps_computed=len(touched_tour_ids),
    )
