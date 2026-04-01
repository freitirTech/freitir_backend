from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.canonical_parser_service import parse_to_canonical_plan

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/canonical")
async def create_canonical_plan(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    try:
        file_bytes = await file.read()
        plan = parse_to_canonical_plan(file.filename, file_bytes)
        return plan.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create canonical plan: {str(exc)}",
        ) from exc