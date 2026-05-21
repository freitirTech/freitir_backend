from fastapi import APIRouter, Depends

from app.core.auth import get_carrier_id
from app.services.analytics_service import get_patterns, get_summary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(carrier_id: str = Depends(get_carrier_id)):
    return get_summary(carrier_id=carrier_id)


@router.get("/patterns")
def analytics_patterns(carrier_id: str = Depends(get_carrier_id)):
    return get_patterns(carrier_id=carrier_id)
