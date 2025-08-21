# schemas/dashboard.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class DashboardOverview(BaseModel):
    user: Dict[str, Any]
    bookings_summary: Dict[str, int]
    notifications: Optional[int] = 0
    analytics: Dict[str, int]
    recent_bookings: List[Dict[str, Any]]
    recent_templates: List[Dict[str, Any]]
    leaderboard: List[Dict[str, Any]]
    active_projects: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
