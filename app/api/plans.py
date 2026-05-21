from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from typing import Optional

from app.core.auth import get_carrier_id
from app.services.canonical_parser_service import parse_to_canonical_plan
from app.services.plan_db_service import save_plan
from app.services.plan_query_service import get_plan_with_gaps, list_plans
from app.services.risk_scoring_service import score_plan

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("")
def get_plans(carrier_id: str = Depends(get_carrier_id)):
    return list_plans(carrier_id=carrier_id)


@router.get("/{plan_id}/gaps")
def get_gaps(plan_id: str, carrier_id: str = Depends(get_carrier_id)):
    result = get_plan_with_gaps(plan_id=plan_id, carrier_id=carrier_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Plan not found.")
    return result


@router.post("/canonical")
async def create_canonical_plan(
    file: UploadFile = File(...),
    plan_date: Optional[str] = Form(None),
    carrier_id: str = Depends(get_carrier_id),
):
    """
    Upload a transport plan CSV/Excel file.
    plan_date (optional, YYYY-MM-DD): the date the tours actually run.
    Defaults to today if omitted.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    try:
        file_bytes = await file.read()
        plan = parse_to_canonical_plan(file.filename, file_bytes)
        db_plan_id = save_plan(plan, carrier_id=carrier_id, plan_date=plan_date)
        score_plan(plan_id=db_plan_id, carrier_id=carrier_id)
        return {**plan.model_dump(), "db_plan_id": db_plan_id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to create canonical plan: {str(exc)}") from exc
