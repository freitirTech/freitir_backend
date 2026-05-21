from fastapi import APIRouter, Depends

from app.core.auth import get_carrier_id
from app.core.supabase_client import get_supabase

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/feed")
def intelligence_feed(carrier_id: str = Depends(get_carrier_id)):
    """
    Returns all tour risks ranked by risk score, with stop-level detail.
    This is the core intelligence feed — "here's what will fail tomorrow and why."
    """
    db = get_supabase()

    tour_risks = (
        db.table("tour_risks")
        .select("id, plan_id, tour_id, risk_score, risk_level, estimated_delay_minutes, estimated_revenue_loss_eur, estimated_co2_kg, flagged_stops, computed_at")
        .eq("carrier_id", carrier_id)
        .order("risk_score", desc=True)
        .execute()
    ).data

    if not tour_risks:
        return []

    tour_risk_ids = [r["id"] for r in tour_risks]
    tour_ids = [r["tour_id"] for r in tour_risks]
    plan_ids = list({r["plan_id"] for r in tour_risks})

    # Load supporting data in parallel lookups
    stop_risks = (
        db.table("stop_risks")
        .select("tour_risk_id, stop_id, location_name, risk_score, avg_historical_delay_minutes, historical_failure_rate, historical_sample_count, recommended_action")
        .in_("tour_risk_id", tour_risk_ids)
        .order("risk_score", desc=True)
        .execute()
    ).data

    tours = (
        db.table("tours")
        .select("id, external_tour_id")
        .in_("id", tour_ids)
        .execute()
    ).data

    plans = (
        db.table("plans")
        .select("id, filename")
        .in_("id", plan_ids)
        .execute()
    ).data

    stop_risks_by_tour_risk: dict[str, list] = {}
    for sr in stop_risks:
        stop_risks_by_tour_risk.setdefault(sr["tour_risk_id"], []).append(sr)

    tour_map = {t["id"]: t["external_tour_id"] for t in tours}
    plan_map = {p["id"]: p["filename"] for p in plans}

    return [
        {
            "tour_risk_id": r["id"],
            "plan_id": r["plan_id"],
            "plan_filename": plan_map.get(r["plan_id"], ""),
            "external_tour_id": tour_map.get(r["tour_id"], ""),
            "risk_score": r["risk_score"],
            "risk_level": r["risk_level"],
            "estimated_delay_minutes": r["estimated_delay_minutes"],
            "estimated_revenue_loss_eur": r["estimated_revenue_loss_eur"],
            "estimated_co2_kg": r["estimated_co2_kg"],
            "flagged_stops": r["flagged_stops"],
            "computed_at": r["computed_at"],
            "stop_risks": stop_risks_by_tour_risk.get(r["id"], []),
        }
        for r in tour_risks
    ]
