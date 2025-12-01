"""
ActionItem Pydantic Schemas

This module defines Pydantic models for action item data validation
and serialization. These schemas are used for API request/response
handling.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.action_item import ActionItemPriority, ActionItemStatus


class ActionItemBase(BaseModel):
    """Base schema with common action item fields."""

    title: str = Field(
        ..., min_length=1, max_length=255, description="Action item title"
    )
    description: Optional[str] = Field(None, description="Detailed description")
    owner: Optional[str] = Field(
        None, max_length=100, description="Person responsible"
    )
    due_date: Optional[datetime] = Field(None, description="Deadline for completion")
    priority: ActionItemPriority = Field(
        ActionItemPriority.MEDIUM, description="Priority level"
    )


class ActionItemCreate(ActionItemBase):
    """Schema for creating a new action item."""

    meeting_id: int = Field(..., description="ID of the parent meeting")


class ActionItemUpdate(BaseModel):
    """E05: Schema for updating an existing action item."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Action item title"
    )
    description: Optional[str] = Field(None, description="Detailed description")
    owner: Optional[str] = Field(
        None, max_length=100, description="Person responsible"
    )
    due_date: Optional[datetime] = Field(None, description="Deadline for completion")
    status: Optional[ActionItemStatus] = Field(None, description="Current status")
    priority: Optional[ActionItemPriority] = Field(None, description="Priority level")
    notes: Optional[str] = Field(None, description="Additional notes or comments")  # E05：新增备注字段


class ActionItemResponse(ActionItemBase):
    """E05: Schema for action item response."""

    id: int
    meeting_id: int
    status: ActionItemStatus
    notes: Optional[str] = None  # E05：备注字段
    is_deleted: bool = False  # E05：软删除标记
    deleted_at: Optional[datetime] = None  # E05：删除时间
    status_changed_at: Optional[datetime] = None  # E05：状态变更时间
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionItemStatusUpdate(BaseModel):
    """Schema for updating action item status only."""

    status: ActionItemStatus = Field(..., description="New status")


class BatchStatusUpdate(BaseModel):
    """E05: Schema for batch status update request."""

    ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of action item IDs to update (max 100)"
    )
    status: ActionItemStatus = Field(..., description="New status for all items")

    @field_validator("ids")
    @classmethod
    def validate_ids_unique(cls, v: List[int]) -> List[int]:
        """E05: Ensure all IDs are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate IDs are not allowed")
        return v


class BatchResponse(BaseModel):
    """E05: Schema for batch operation response."""

    updated_count: int = Field(..., description="Number of items updated")
    ids: List[int] = Field(..., description="List of IDs that were processed")
    message: str = Field(..., description="Result message")

