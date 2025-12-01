"""
Pydantic Schemas Package

This package contains all Pydantic schemas for API validation and serialization.
"""

from app.schemas.action_item import (
    ActionItemBase,
    ActionItemCreate,
    ActionItemResponse,
    ActionItemStatusUpdate,
    ActionItemUpdate,
)
from app.schemas.meeting import (
    MeetingBase,
    MeetingCreate,
    MeetingListResponse,
    MeetingResponse,
    MeetingUpdate,
)

__all__ = [
    # Meeting schemas
    "MeetingBase",
    "MeetingCreate",
    "MeetingUpdate",
    "MeetingResponse",
    "MeetingListResponse",
    # ActionItem schemas
    "ActionItemBase",
    "ActionItemCreate",
    "ActionItemUpdate",
    "ActionItemResponse",
    "ActionItemStatusUpdate",
]
