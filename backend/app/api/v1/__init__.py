"""
API v1 Router

This module sets up the main API v1 router and includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import action_items, meetings

router = APIRouter()

# Include endpoint routers with their prefixes and tags
router.include_router(
    meetings.router,
    prefix="/meetings",
    tags=["Meetings"],
)

router.include_router(
    action_items.router,
    prefix="/action-items",
    tags=["Action Items"],
)
