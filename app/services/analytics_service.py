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
