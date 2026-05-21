from app.core.supabase_client import get_supabase
from app.services.financial_service import co2_kg, revenue_lost_eur

PATTERN_LIMIT = 20


def get_summary(carrier_id: str) -> dict:
    db = get_supabase()

    # Total delay across all tour_gaps for this carrier
    tour_gaps = (
        db.table("tour_gaps")
        .select("tour_id, total_delay_minutes, failed_stops, total_stops")
        .eq("carrier_id", carrier_id)
        .execute()
    ).data

    total_delay = sum(t["total_delay_minutes"] for t in tour_gaps)
    total_failed = sum(t["failed_stops"] for t in tour_gaps)
    total_stops = sum(t["total_stops"] for t in tour_gaps)

    # Count distinct plans
    tour_ids = [t["tour_id"] for t in tour_gaps]
    plans_count = 0
    if tour_ids:
        tours = db.table("tours").select("plan_id").in_("id", tour_ids).execute().data
        plans_count = len({t["plan_id"] for t in tours})

    # Worst locations from patterns table
    patterns = (
        db.table("patterns")
        .select("location_name, avg_arrival_delta_minutes, failure_rate, sample_count")
        .eq("carrier_id", carrier_id)
        .order("avg_arrival_delta_minutes", desc=True)
        .limit(5)
        .execute()
    ).data

    return {
        "total_delay_minutes": total_delay,
        "revenue_lost_eur": revenue_lost_eur(total_delay),
        "co2_kg": co2_kg(total_delay),
        "tours_analyzed": len(tour_gaps),
        "plans_analyzed": plans_count,
        "total_failed_stops": total_failed,
        "total_stops": total_stops,
        "worst_locations": patterns,
    }


def get_weekly_trends(carrier_id: str) -> list[dict]:
    """
    Return week-by-week performance grouped by plan_date.
    Only includes plans that have a plan_date set and have execution data.
    """
    db = get_supabase()

    # Plans with dates, oldest first
    plans = (
        db.table("plans")
        .select("id, plan_date, filename")
        .eq("carrier_id", carrier_id)
        .not_.is_("plan_date", "null")
        .order("plan_date")
        .execute()
    ).data

    if not plans:
        return []

    plan_ids = [p["id"] for p in plans]
    plan_by_id = {p["id"]: p for p in plans}

    # Tours for those plans
    tours = (
        db.table("tours")
        .select("id, plan_id")
        .in_("plan_id", plan_ids)
        .execute()
    ).data

    tour_to_plan: dict[str, str] = {t["id"]: t["plan_id"] for t in tours}
    tour_ids = list(tour_to_plan.keys())

    if not tour_ids:
        return []

    # Tour gaps (already aggregated per tour)
    tour_gaps = (
        db.table("tour_gaps")
        .select("tour_id, total_delay_minutes, failed_stops, total_stops")
        .in_("tour_id", tour_ids)
        .execute()
    ).data

    # Group by plan_date
    from collections import defaultdict
    by_date: dict[str, dict] = defaultdict(
        lambda: {"total_delay_minutes": 0, "failed_stops": 0, "total_stops": 0, "tours_run": 0}
    )

    for tg in tour_gaps:
        plan_id = tour_to_plan.get(tg["tour_id"])
        if not plan_id:
            continue
        plan_date = plan_by_id[plan_id]["plan_date"]
        d = by_date[plan_date]
        d["total_delay_minutes"] += tg["total_delay_minutes"]
        d["failed_stops"] += tg["failed_stops"]
        d["total_stops"] += tg["total_stops"]
        d["tours_run"] += 1

    return [
        {
            "plan_date": date,
            "tours_run": data["tours_run"],
            "total_delay_minutes": data["total_delay_minutes"],
            "failed_stops": data["failed_stops"],
            "total_stops": data["total_stops"],
            "revenue_lost_eur": revenue_lost_eur(data["total_delay_minutes"]),
        }
        for date, data in sorted(by_date.items())
    ]


def get_patterns(carrier_id: str) -> list[dict]:
    db = get_supabase()
    return (
        db.table("patterns")
        .select("location_name, avg_arrival_delta_minutes, failure_rate, sample_count, computed_at")
        .eq("carrier_id", carrier_id)
        .order("avg_arrival_delta_minutes", desc=True)
        .limit(PATTERN_LIMIT)
        .execute()
    ).data
