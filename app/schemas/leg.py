from pydantic import BaseModel


class Leg(BaseModel):
    leg_id: str
    from_stop_id: str
    to_stop_id: str