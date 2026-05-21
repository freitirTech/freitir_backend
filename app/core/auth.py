from fastapi import Depends, Header, HTTPException
from app.core.supabase_client import get_supabase


async def get_carrier_id(authorization: str = Header(...)) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    db = get_supabase()

    try:
        user_response = db.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    member = (
        db.table("carrier_members")
        .select("carrier_id")
        .eq("user_id", user_id)
        .execute()
    )
    if not member.data:
        raise HTTPException(status_code=403, detail="Onboarding incomplete. Please set up your company first.")

    return member.data[0]["carrier_id"]
