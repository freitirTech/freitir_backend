from io import BytesIO

import pandas as pd

from app.schemas.execution import ExecutionEventIn


REQUIRED_COLUMNS = ["tour_id", "stop_sequence"]


def _str_or_none(val) -> str | None:
    """Return stripped string, or None for any null-like value (None, NaN, empty)."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None


def parse_execution_csv(filename: str, file_bytes: bytes) -> list[ExecutionEventIn]:
    lower = filename.lower()

    if lower.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
    elif lower.endswith(".xlsx") or lower.endswith(".xls"):
        df = pd.read_excel(BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")

    df.columns = [str(col).strip() for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    events: list[ExecutionEventIn] = []
    for _, row in df.iterrows():
        events.append(ExecutionEventIn(
            tour_id=str(row["tour_id"]),
            stop_sequence=int(row["stop_sequence"]),
            actual_arrival=_str_or_none(row.get("actual_arrival")),
            actual_departure=_str_or_none(row.get("actual_departure")),
            status=_str_or_none(row.get("status")) or "completed",
            failure_reason=_str_or_none(row.get("failure_reason")),
        ))

    return events
