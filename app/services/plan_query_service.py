from app.core.supabase_client import get_supabase


def list_plans(carrier_id: str) -> list[dict]:
    db = get_supabase()

    plans = db.table("plans").select("id, filename, uploaded_at").eq("carrier_id", carrier_id).order("uploaded_at", desc=True).execute()

    tour_counts = db.table("tours").select("id, plan_id").eq("carrier_id", carrier_id).execute()
    execution_stop_ids = {e["stop_id"] for e in db.table("execution_events").select("stop_id").eq("carrier_id", carrier_id).execute().data}
    stops = db.table("stops").select("id, tour_id").eq("carrier_id", carrier_id).execute().data
    tours_with_execution = {
        s["tour_id"]
        for s in stops
        if s["id"] in execution_stop_ids
    }
    plans_with_execution = {
        t["plan_id"]
        for t in tour_counts.data
        if t["id"] in tours_with_execution
    }

    counts_by_plan: dict[str, int] = {}
    for t in tour_counts.data:
        counts_by_plan[t["plan_id"]] = counts_by_plan.get(t["plan_id"], 0) + 1

    return [
        {
            "id": p["id"],
            "filename": p["filename"],
            "uploaded_at": p["uploaded_at"],
            "tour_count": counts_by_plan.get(p["id"], 0),
            "has_execution": p["id"] in plans_with_execution,
        }
        for p in plans.data
    ]


def get_plan_with_gaps(plan_id: str, carrier_id: str) -> dict | None:
    db = get_supabase()

    plan_res = db.table("plans").select("id, filename, uploaded_at").eq("id", plan_id).eq("carrier_id", carrier_id).execute()
    if not plan_res.data:
        return None
    plan = plan_res.data[0]

    tours = db.table("tours").select("id, external_tour_id").eq("plan_id", plan_id).eq("carrier_id", carrier_id).order("external_tour_id").execute().data
    tour_ids = [t["id"] for t in tours]

    stops = db.table("stops").select("id, tour_id, sequence, location_name, planned_arrival, planned_departure").in_("tour_id", tour_ids).order("sequence").execute().data
    stop_ids = [s["id"] for s in stops]

    stop_gaps = db.table("stop_gaps").select("stop_id, arrival_delta_minutes, departure_delta_minutes, is_failed").in_("stop_id", stop_ids).execute().data
    tour_gaps = db.table("tour_gaps").select("tour_id, total_delay_minutes, failed_stops, total_stops").in_("tour_id", tour_ids).execute().data

    gap_by_stop = {g["stop_id"]: g for g in stop_gaps}
    gap_by_tour = {g["tour_id"]: g for g in tour_gaps}

    stops_by_tour: dict[str, list] = {}
    for stop in stops:
        gap = gap_by_stop.get(stop["id"])
        stops_by_tour.setdefault(stop["tour_id"], []).append({
            "db_stop_id": stop["id"],
            "sequence": stop["sequence"],
            "location_name": stop["location_name"],
            "planned_arrival": stop["planned_arrival"],
            "planned_departure": stop["planned_departure"],
            "gap": {
                "arrival_delta_minutes": gap["arrival_delta_minutes"] if gap else None,
                "departure_delta_minutes": gap["departure_delta_minutes"] if gap else None,
                "is_failed": gap["is_failed"] if gap else False,
            } if gap else None,
        })

    return {
        "plan_id": plan["id"],
        "filename": plan["filename"],
        "uploaded_at": plan["uploaded_at"],
        "tours": [
            {
                "db_tour_id": t["id"],
                "external_tour_id": t["external_tour_id"],
                "gap": gap_by_tour.get(t["id"]),
                "stops": stops_by_tour.get(t["id"], []),
            }
            for t in tours
        ],
    }
