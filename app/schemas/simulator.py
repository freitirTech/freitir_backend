from typing import Literal
from pydantic import BaseModel


class SimulatorRunRequest(BaseModel):
    plan_id: str
    scenario: Literal["on_time", "delayed", "disrupted"]


class SimulatorRunResult(BaseModel):
    plan_id: str
    scenario: str
    events_generated: int
    stop_gaps_computed: int
    tour_gaps_computed: int
