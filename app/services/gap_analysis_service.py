from datetime import datetime, timezone


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        # Normalise to UTC so planned (from DB, has tz) and actual (from CSV, naive) are comparable
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


def _delta_minutes(actual: str | None, planned: str | None) -> int | None:
    a, p = _parse_dt(actual), _parse_dt(planned)
    if a is None or p is None:
        return None
    return int((a - p).total_seconds() / 60)


def compute_stop_gaps(
    db,
    carrier_id: str,
    execution_event_id: str,
    stop_id: str,
    actual_arrival: str | None,
    actual_departure: str | None,
    planned_arrival: str | None,
    planned_departure: str | None,
    is_failed: bool,
) -> None:
    db.table("stop_gaps").insert({
        "carrier_id": carrier_id,
        "stop_id": stop_id,
        "execution_event_id": execution_event_id,
        "arrival_delta_minutes": _delta_minutes(actual_arrival, planned_arrival),
        "departure_delta_minutes": _delta_minutes(actual_departure, planned_departure),
        "is_failed": is_failed,
    }).execute()


def compute_tour_gaps(db, carrier_id: str, tour_id: str) -> None:
    stop_gaps = (
        db.table("stop_gaps")
        .select("arrival_delta_minutes, is_failed, stop_id")
        .eq("carrier_id", carrier_id)
        .execute()
    )

    # Filter to stops belonging to this tour
    tour_stops = (
        db.table("stops")
        .select("id")
        .eq("tour_id", tour_id)
        .execute()
    )
    tour_stop_ids = {row["id"] for row in tour_stops.data}

    relevant_gaps = [g for g in stop_gaps.data if g["stop_id"] in tour_stop_ids]

    total_delay = sum(
        g["arrival_delta_minutes"]
        for g in relevant_gaps
        if g["arrival_delta_minutes"] and g["arrival_delta_minutes"] > 0
    )
    failed_stops = sum(1 for g in relevant_gaps if g["is_failed"])

    db.table("tour_gaps").insert({
        "carrier_id": carrier_id,
        "tour_id": tour_id,
        "total_delay_minutes": total_delay,
        "failed_stops": failed_stops,
        "total_stops": len(tour_stop_ids),
    }).execute()
