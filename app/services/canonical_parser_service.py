from io import BytesIO
from uuid import uuid4

import pandas as pd

from app.schemas.leg import Leg
from app.schemas.plan import Plan
from app.schemas.stop import Stop
from app.schemas.tour import Tour


REQUIRED_COLUMNS = [
    "tour_id",
    "stop_sequence",
    "location",
]


OPTIONAL_COLUMNS = [
    "planned_arrival",
    "planned_departure",
]


def parse_to_canonical_plan(filename: str, file_bytes: bytes) -> Plan:
    lower_name = filename.lower()

    if lower_name.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
    elif lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
        df = pd.read_excel(BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file type. Please upload a CSV or Excel file.")

    df.columns = [str(col).strip() for col in df.columns]

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

    df = df.where(pd.notnull(df), None)

    tours: list[Tour] = []

    grouped = df.groupby("tour_id", dropna=False)

    for raw_tour_id, group in grouped:
        group = group.sort_values("stop_sequence")
        tour_id = str(raw_tour_id)

        stops: list[Stop] = []
        for _, row in group.iterrows():
            sequence = int(row["stop_sequence"])
            stop_id = f"{tour_id}_stop_{sequence}"

            stop = Stop(
                stop_id=stop_id,
                sequence=sequence,
                location_name=str(row["location"]),
                planned_arrival=(
                    str(row["planned_arrival"])
                    if "planned_arrival" in row and row["planned_arrival"] is not None
                    else None
                ),
                planned_departure=(
                    str(row["planned_departure"])
                    if "planned_departure" in row and row["planned_departure"] is not None
                    else None
                ),
            )
            stops.append(stop)

        legs: list[Leg] = []
        for i in range(len(stops) - 1):
            leg = Leg(
                leg_id=f"{tour_id}_leg_{i+1}",
                from_stop_id=stops[i].stop_id,
                to_stop_id=stops[i + 1].stop_id,
            )
            legs.append(leg)

        tours.append(
            Tour(
                tour_id=tour_id,
                stops=stops,
                legs=legs,
            )
        )

    return Plan(
        plan_id=str(uuid4()),
        filename=filename,
        tours=tours,
    )