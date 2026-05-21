from datetime import datetime, timedelta, timezone

from app.core.supabase_client import get_supabase


def compute_patterns(carrier_id: str) -> int:
    """
    Recompute rolling 6-week location patterns for a carrier.
    Aggregates stop_gaps → stops to get per-location stats.
    Returns the number of pattern rows upserted.
    """
    db = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(weeks=6)).isoformat()

    # Pull all stop_gaps created within the 6-week window for this carrier
    gaps = (
        db.table("stop_gaps")
        .select("stop_id, arrival_delta_minutes, is_failed, computed_at")
        .eq("carrier_id", carrier_id)
        .gte("computed_at", cutoff)
        .execute()
    ).data

    if not gaps:
        return 0

    # Fetch location names for all referenced stops in one query
    stop_ids = list({g["stop_id"] for g in gaps})
    stops = (
        db.table("stops")
        .select("id, location_name")
        .in_("id", stop_ids)
        .execute()
    ).data

    location_by_stop: dict[str, str] = {s["id"]: s["location_name"] for s in stops}

    # Aggregate per location
    stats: dict[str, dict] = {}
    for gap in gaps:
        loc = location_by_stop.get(gap["stop_id"])
        if not loc:
            continue
        if loc not in stats:
            stats[loc] = {"deltas": [], "failures": 0, "total": 0}
        stats[loc]["total"] += 1
        if gap["arrival_delta_minutes"] is not None:
            stats[loc]["deltas"].append(gap["arrival_delta_minutes"])
        if gap["is_failed"]:
            stats[loc]["failures"] += 1

    if not stats:
        return 0

    rows = [
        {
            "carrier_id": carrier_id,
            "location_name": loc,
            "sample_count": data["total"],
            "avg_arrival_delta_minutes": (
                round(sum(data["deltas"]) / len(data["deltas"]), 2)
                if data["deltas"] else None
            ),
            "failure_rate": round(data["failures"] / data["total"], 4),
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        for loc, data in stats.items()
    ]

    # Upsert — update existing pattern rows for this carrier+location
    db.table("patterns").upsert(rows, on_conflict="carrier_id,location_name").execute()

    return len(rows)
