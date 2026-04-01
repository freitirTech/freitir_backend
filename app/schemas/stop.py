from pydantic import BaseModel


class Stop(BaseModel):
    stop_id: str
    sequence: int
    location_name: str
    planned_arrival: str | None = None
    planned_departure: str | None = None