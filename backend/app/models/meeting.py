"""
Meeting Database Model

This module defines the Meeting model representing a meeting record
in the database. A meeting contains the original text content, AI-generated
summary, and associated action items.
"""

import json
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.action_item import ActionItem


class MeetingStatus(str, Enum):
    """
    Enumeration of meeting processing statuses.

    - DRAFT: Meeting created but not yet processed
    - PROCESSING: AI is generating the summary
    - COMPLETED: Summary generation completed
    """

    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"


class Meeting(Base):
    """
    Meeting model representing a meeting record.

    Attributes:
        id: Primary key
        title: Meeting title (required, indexed for search)
        start_time: Meeting start time (optional)
        end_time: Meeting end time (optional)
        original_text: Original meeting content/transcript (up to 50,000 chars)
        summary: AI-generated meeting summary (plain text overview)
        topics: JSON array of core topics discussed
        decisions: JSON array of decisions made
        discussion_points: JSON array of key discussion points
        status: Processing status (draft/processing/completed)
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
        action_items: Related action items (one-to-many relationship)
    """

    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    participants: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Content fields
    original_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Structured summary fields (stored as JSON strings)
    topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decisions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discussion_points: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), default=MeetingStatus.DRAFT.value, nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    action_items: Mapped[List["ActionItem"]] = relationship(
        "ActionItem",
        back_populates="meeting",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Meeting(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def topics_list(self) -> List[str]:
        """Parse topics JSON string to list."""
        if self.topics:
            try:
                return json.loads(self.topics)
            except json.JSONDecodeError:
                return []
        return []
    
    @property
    def decisions_list(self) -> List[str]:
        """Parse decisions JSON string to list."""
        if self.decisions:
            try:
                return json.loads(self.decisions)
            except json.JSONDecodeError:
                return []
        return []
    
    @property
    def discussion_points_list(self) -> List[str]:
        """Parse discussion_points JSON string to list."""
        if self.discussion_points:
            try:
                return json.loads(self.discussion_points)
            except json.JSONDecodeError:
                return []
        return []
