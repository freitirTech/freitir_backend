from app.core.supabase_client import get_supabase
from app.services.financial_service import co2_kg, revenue_lost_eur
from app.services.recommendation_service import get_recommendation


def _delay_score(avg_delay: float | None) -> float:
    if not avg_delay or avg_delay <= 0:
        return 0.0
    if avg_delay <= 15:
        return 0.2
    if avg_delay <= 30:
        return 0.5
    if avg_delay <= 60:
        return 0.7
    return 1.0


def _failure_score(failure_rate: float | None) -> float:
    if not failure_rate:
        return 0.0
    # Failure is weighted heavier than delay — cap at 1.0
    return min(failure_rate * 1.5, 1.0)


def _risk_level(score: float) -> str:
    if score >= 0.5:
        return "high"
    if score >= 0.2:
        return "medium"
    return "low"


def score_plan(plan_id: str, carrier_id: str) -> int:
    """
    Score all tours in a plan against historical patterns.
    Upserts tour_risks + stop_risks. Returns number of tours scored.
    """
    db = get_supabase()

    # Load tours for this plan
    tours = (
        db.table("tours")
        .select("id, external_tour_id")
        .eq("plan_id", plan_id)
        .eq("carrier_id", carrier_id)
        .execute()
    ).data

    if not tours:
        return 0

    tour_ids = [t["id"] for t in tours]

    # Load stops for all tours in one query
    stops = (
        db.table("stops")
        .select("id, tour_id, sequence, location_name")
        .in_("tour_id", tour_ids)
        .order("sequence")
        .execute()
    ).data

    # Load patterns for all locations in one query
    locations = list({s["location_name"] for s in stops})
    pattern_rows = (
        db.table("patterns")
        .select("location_name, avg_arrival_delta_minutes, failure_rate, sample_count")
        .eq("carrier_id", carrier_id)
        .in_("location_name", locations)
        .execute()
    ).data

    pattern_by_location: dict[str, dict] = {p["location_name"]: p for p in pattern_rows}
    stops_by_tour: dict[str, list] = {}
    for stop in stops:
        stops_by_tour.setdefault(stop["tour_id"], []).append(stop)

    tours_scored = 0

    for tour in tours:
        tour_stops = stops_by_tour.get(tour["id"], [])
        if not tour_stops:
            continue

        stop_risk_rows = []
        stop_scores = []
        total_estimated_delay = 0

        for stop in tour_stops:
            pattern = pattern_by_location.get(stop["location_name"])
            avg_delay = float(pattern["avg_arrival_delta_minutes"]) if pattern and pattern["avg_arrival_delta_minutes"] else None
            failure_rate = float(pattern["failure_rate"]) if pattern and pattern["failure_rate"] else None
            sample_count = pattern["sample_count"] if pattern else 0

            d_score = _delay_score(avg_delay)
            f_score = _failure_score(failure_rate)
            stop_score = round((d_score + f_score) / 2, 4)
            stop_scores.append(stop_score)

            if avg_delay and avg_delay > 0:
                total_estimated_delay += int(avg_delay)

            stop_risk_rows.append({
                "stop_id": stop["id"],
                "location_name": stop["location_name"],
                "risk_score": stop_score,
                "avg_historical_delay_minutes": avg_delay,
                "historical_failure_rate": failure_rate,
                "historical_sample_count": sample_count,
                "recommended_action": get_recommendation(stop["location_name"], avg_delay, failure_rate),
            })

        tour_score = round(sum(stop_scores) / len(stop_scores), 4) if stop_scores else 0.0
        flagged = sum(1 for s in stop_risk_rows if s["risk_score"] >= 0.2)

        # Delete any existing tour_risk for this tour, then insert fresh
        db.table("tour_risks").delete().eq("tour_id", tour["id"]).execute()
        tour_risk_res = db.table("tour_risks").insert({
            "carrier_id": carrier_id,
            "plan_id": plan_id,
            "tour_id": tour["id"],
            "risk_score": tour_score,
            "risk_level": _risk_level(tour_score),
            "estimated_delay_minutes": total_estimated_delay,
            "estimated_revenue_loss_eur": revenue_lost_eur(total_estimated_delay),
            "estimated_co2_kg": co2_kg(total_estimated_delay),
            "flagged_stops": flagged,
        }).execute()

        tour_risk_id = tour_risk_res.data[0]["id"]

        # Delete old stop_risks for this tour_risk and insert fresh
        db.table("stop_risks").delete().eq("tour_risk_id", tour_risk_id).execute()

        for row in stop_risk_rows:
            db.table("stop_risks").insert({
                **row,
                "carrier_id": carrier_id,
                "tour_risk_id": tour_risk_id,
            }).execute()

        tours_scored += 1

    return tours_scored
