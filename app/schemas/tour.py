from pydantic import BaseModel

from app.schemas.leg import Leg
from app.schemas.stop import Stop


class Tour(BaseModel):
    tour_id: str
    stops: list[Stop]
    legs: list[Leg]