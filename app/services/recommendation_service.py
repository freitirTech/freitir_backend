def get_recommendation(
    location: str,
    avg_delay: float | None,
    failure_rate: float | None,
) -> str:
    """Return one plain-English recommended action for a stop."""
    has_delay = avg_delay is not None and avg_delay > 0
    has_failures = failure_rate is not None and failure_rate > 0

    if failure_rate and failure_rate >= 0.3:
        return f"Call ahead to {location} before dispatch — fails {int(failure_rate * 100)}% of runs"

    if has_delay and has_failures:
        return (
            f"Buffer +{int(avg_delay)} min at {location} "
            f"and monitor for failure ({int(failure_rate * 100)}% failure rate)"
        )

    if avg_delay and avg_delay > 30:
        return f"Add {int(avg_delay)} min buffer before {location} — consistently runs late"

    if avg_delay and avg_delay > 10:
        return f"Expect ~{int(avg_delay)} min delay at {location} based on recent runs"

    if has_failures:
        return f"Monitor {location} — occasional failures recorded"

    return f"No significant risk at {location}"
