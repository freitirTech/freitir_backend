from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.core.supabase_client import get_supabase

router = APIRouter(prefix="/carriers", tags=["carriers"])


class OnboardRequest(BaseModel):
    name: str


@router.post("/onboard")
async def onboard(body: OnboardRequest, authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ").strip()
    db = get_supabase()

    try:
        user_response = db.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    existing = (
        db.table("carrier_members")
        .select("carrier_id")
        .eq("user_id", user_id)
        .execute()
    )
    if existing.data:
        return {"carrier_id": existing.data[0]["carrier_id"]}

    carrier = db.table("carriers").insert({"name": body.name}).execute()
    carrier_id: str = carrier.data[0]["id"]

    db.table("carrier_members").insert({
        "carrier_id": carrier_id,
        "user_id": user_id,
        "role": "admin",
    }).execute()

    return {"carrier_id": carrier_id}
