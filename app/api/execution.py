from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.core.auth import get_carrier_id
from app.schemas.execution import ExecutionUploadResult
from app.services.execution_db_service import save_execution
from app.services.execution_parser_service import parse_execution_csv

router = APIRouter(prefix="/execution", tags=["execution"])


@router.post("/upload", response_model=ExecutionUploadResult)
async def upload_execution(
    file: UploadFile = File(...),
    plan_id: str = Query(..., description="DB plan ID returned when the plan was uploaded"),
    carrier_id: str = Depends(get_carrier_id),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    try:
        file_bytes = await file.read()
        events = parse_execution_csv(file.filename, file_bytes)
        return save_execution(plan_id=plan_id, carrier_id=carrier_id, events=events)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process execution data: {str(exc)}") from exc
