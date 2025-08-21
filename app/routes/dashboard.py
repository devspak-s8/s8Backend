# app/routes/dashboard_router.py
from fastapi import APIRouter, Depends
from app.dashboard_service import get_dashboard_overview
from app.middleware.rbac import get_current_user

dashboard_router = APIRouter(tags=["Dashboard"])

@dashboard_router.get("/overview")
async def dashboard_overview(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    return await get_dashboard_overview(user_id)
