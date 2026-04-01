from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.parser_service import parse_uploaded_file

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/plan")
async def upload_plan(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    try:
        file_bytes = await file.read()
        parsed = parse_uploaded_file(file.filename, file_bytes)
        return parsed
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {str(exc)}") from exc