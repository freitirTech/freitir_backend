from pydantic import BaseModel


class ExecutionEventIn(BaseModel):
    tour_id: str
    stop_sequence: int
    actual_arrival: str | None = None
    actual_departure: str | None = None
    status: str = "completed"  # 'completed' | 'failed' | 'partial'
    failure_reason: str | None = None


class ExecutionUploadResult(BaseModel):
    plan_id: str
    events_saved: int
    stop_gaps_computed: int
    tour_gaps_computed: int
