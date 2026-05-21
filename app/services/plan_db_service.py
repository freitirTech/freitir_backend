from app.core.supabase_client import get_supabase
from app.schemas.plan import Plan


def save_plan(plan: Plan, carrier_id: str, plan_date: str | None = None) -> str:
    """
    Persists a canonical Plan (tours → stops → legs) to Supabase.
    Returns the DB-assigned plan UUID.
    """
    db = get_supabase()

    plan_payload: dict = {"carrier_id": carrier_id, "filename": plan.filename}
    if plan_date:
        plan_payload["plan_date"] = plan_date

    plan_row = (
        db.table("plans")
        .insert(plan_payload)
        .execute()
    )
    db_plan_id: str = plan_row.data[0]["id"]

    for tour in plan.tours:
        tour_row = (
            db.table("tours")
            .insert({
                "plan_id": db_plan_id,
                "carrier_id": carrier_id,
                "external_tour_id": tour.tour_id,
            })
            .execute()
        )
        db_tour_id: str = tour_row.data[0]["id"]

        # Map canonical stop_id → DB UUID so legs can reference them
        stop_id_map: dict[str, str] = {}

        for stop in tour.stops:
            stop_row = (
                db.table("stops")
                .insert({
                    "tour_id": db_tour_id,
                    "carrier_id": carrier_id,
                    "sequence": stop.sequence,
                    "location_name": stop.location_name,
                    "planned_arrival": stop.planned_arrival,
                    "planned_departure": stop.planned_departure,
                })
                .execute()
            )
            db_stop_id: str = stop_row.data[0]["id"]
            stop_id_map[stop.stop_id] = db_stop_id

        for i, leg in enumerate(tour.legs):
            db.table("legs").insert({
                "tour_id": db_tour_id,
                "carrier_id": carrier_id,
                "from_stop_id": stop_id_map[leg.from_stop_id],
                "to_stop_id": stop_id_map[leg.to_stop_id],
                "sequence": i + 1,
            }).execute()

    return db_plan_id
