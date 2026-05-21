from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_carrier_id
from app.schemas.simulator import SimulatorRunRequest, SimulatorRunResult
from app.services.simulator_service import run_simulation

router = APIRouter(prefix="/simulator", tags=["simulator"])


@router.post("/run", response_model=SimulatorRunResult)
def simulate_execution(
    req: SimulatorRunRequest,
    carrier_id: str = Depends(get_carrier_id),
) -> SimulatorRunResult:
    """
    Generate synthetic execution data for a plan and run it through the full
    gap-analysis + pattern-refresh + risk-scoring pipeline.

    Scenarios:
      on_time   — minor variation, no meaningful delays
      delayed   — 20–45 min base delay cascading across stops
      disrupted — random failures + moderate delays
    """
    result = run_simulation(
        plan_id=req.plan_id,
        carrier_id=carrier_id,
        scenario=req.scenario,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Plan not found or has no tours.")
    return result
