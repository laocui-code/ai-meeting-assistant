"""
ActionItem Database Model

This module defines the ActionItem model representing a task or action
extracted from a meeting. Action items have status, priority, owner,
and due date for tracking completion.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.meeting import Meeting


class ActionItemStatus(str, Enum):
    """
    Enumeration of action item statuses.

    - TODO: Not started
    - IN_PROGRESS: Currently being worked on
    - DONE: Completed
    - CANCELLED: No longer needed
    """

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

    @classmethod
    def is_valid_transition(cls, from_status: str, to_status: str) -> bool:
        """
        E05: Check if a status transition is allowed.

        Valid transitions:
        - todo -> in_progress, done, cancelled
        - in_progress -> todo, done, cancelled
        - done -> in_progress (reopen)
        - cancelled -> todo (reactivate)

        Invalid transitions:
        - done -> cancelled (completed items shouldn't be cancelled)
        - cancelled -> in_progress, done (must go through todo first)

        Args:
            from_status: Current status value
            to_status: Target status value

        Returns:
            True if transition is valid, False otherwise
        """
        # Same status is always valid (no-op)
        if from_status == to_status:
            return True

        invalid_transitions = {
            (cls.DONE.value, cls.CANCELLED.value),
            (cls.CANCELLED.value, cls.IN_PROGRESS.value),
            (cls.CANCELLED.value, cls.DONE.value),
        }
        return (from_status, to_status) not in invalid_transitions


class ActionItemPriority(str, Enum):
    """
    Enumeration of action item priorities.

    - HIGH: Urgent/important tasks
    - MEDIUM: Normal priority
    - LOW: Can be deferred
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionItem(Base):
    """
    ActionItem model representing a task extracted from a meeting.

    Attributes:
        id: Primary key
        meeting_id: Foreign key to the parent meeting
        title: Action item title (required)
        description: Detailed description (optional)
        owner: Person responsible for this action item
        due_date: Deadline for completion
        status: Current status (todo/in_progress/done/cancelled)
        priority: Priority level (high/medium/low)
        notes: Additional notes or comments
        is_deleted: Soft delete flag
        deleted_at: When the item was soft deleted
        status_changed_at: When status was last changed
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
        meeting: Parent meeting (many-to-one relationship)
    """

    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )

    # Core fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status and priority
    status: Mapped[str] = mapped_column(
        String(50), default=ActionItemStatus.TODO.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(50), default=ActionItemPriority.MEDIUM.value, nullable=False
    )

    # E05：备注字段，用于记录额外信息
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # E05：软删除字段
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # E05：状态变更追踪
    status_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="action_items")

    def __repr__(self) -> str:
        return f"<ActionItem(id={self.id}, title='{self.title}', status='{self.status}')>"
