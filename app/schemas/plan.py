from pydantic import BaseModel

from app.schemas.tour import Tour


class Plan(BaseModel):
    plan_id: str
    filename: str
    tours: list[Tour]