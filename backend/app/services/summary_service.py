"""
Meeting Summary Service

This module provides the service layer for generating AI-powered meeting summaries.
It orchestrates the flow from meeting content to structured summary using the LLM service.
"""

import json
import logging
from typing import Optional

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting, MeetingStatus
from app.services.llm_service import (
    LLMService,
    LLMError,
    LLMResponseParseError,
    get_llm_service,
)
from app.services.prompts import MeetingSummaryOutput, build_summary_prompt

logger = logging.getLogger(__name__)


class SummaryGenerationError(Exception):
    """Raised when summary generation fails."""
    pass


class MeetingNotFoundError(Exception):
    """Raised when meeting is not found."""
    pass


class MeetingSummaryService:
    """
    Service for generating AI-powered meeting summaries.
    
    This service handles the complete flow of:
    1. Loading meeting from database
    2. Building prompts with meeting content
    3. Calling LLM for summary generation
    4. Parsing and validating the response
    5. Storing results back to database
    """
    
    def __init__(self, db: AsyncSession, llm_service: Optional[LLMService] = None):
        """
        Initialize the summary service.
        
        Args:
            db: Async database session
            llm_service: Optional LLM service instance (uses singleton if not provided)
        """
        self.db = db
        self.llm = llm_service or get_llm_service()
    
    async def generate_summary(self, meeting_id: int) -> Meeting:
        """
        Generate a structured summary for a meeting.
        
        This is the main entry point for summary generation. It:
        1. Loads the meeting from database
        2. Validates that it has content to summarize
        3. Updates status to 'processing'
        4. Generates summary using LLM
        5. Stores results and updates status to 'completed'
        
        Args:
            meeting_id: ID of the meeting to summarize
            
        Returns:
            Updated Meeting object with generated summary
            
        Raises:
            MeetingNotFoundError: If meeting doesn't exist
            SummaryGenerationError: If generation fails
        """
        # Load meeting
        meeting = await self._get_meeting(meeting_id)
        if not meeting:
            raise MeetingNotFoundError(f"Meeting with id {meeting_id} not found")
        
        # Validate content exists
        if not meeting.original_text or not meeting.original_text.strip():
            raise SummaryGenerationError(
                "Meeting has no content to summarize. Please add original_text first."
            )
        
        # Update status to processing
        meeting.status = MeetingStatus.PROCESSING.value
        await self.db.flush()
        
        try:
            # Generate summary
            summary_output = await self._generate_summary_from_llm(meeting)
            
            # Store results
            meeting.summary = summary_output.summary
            meeting.topics = json.dumps(summary_output.topics, ensure_ascii=False)
            meeting.decisions = json.dumps(summary_output.decisions, ensure_ascii=False)
            meeting.discussion_points = json.dumps(
                summary_output.discussion_points, ensure_ascii=False
            )
            meeting.status = MeetingStatus.COMPLETED.value
            
            await self.db.flush()
            logger.info(f"Successfully generated summary for meeting {meeting_id}")
            
            return meeting
            
        except Exception as e:
            # Revert status on failure
            meeting.status = MeetingStatus.DRAFT.value
            await self.db.flush()
            
            logger.error(f"Failed to generate summary for meeting {meeting_id}: {e}")
            raise SummaryGenerationError(f"Summary generation failed: {e}")
    
    async def _get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        """Load a meeting from the database."""
        result = await self.db.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        return result.scalar_one_or_none()
    
    async def _generate_summary_from_llm(self, meeting: Meeting) -> MeetingSummaryOutput:
        """
        Generate summary using LLM.
        
        Args:
            meeting: Meeting object with content
            
        Returns:
            Validated MeetingSummaryOutput object
            
        Raises:
            SummaryGenerationError: If LLM call or parsing fails
        """
        # Format meeting time
        meeting_time = None
        if meeting.start_time:
            meeting_time = meeting.start_time.strftime("%Y-%m-%d %H:%M")
            if meeting.end_time:
                meeting_time += f" - {meeting.end_time.strftime('%H:%M')}"
        
        # Build prompt messages
        messages = build_summary_prompt(
            title=meeting.title,
            content=meeting.original_text,
            meeting_time=meeting_time,
            participants=None,  # Will be added in V2 when we have participant management
        )
        
        try:
            # Call LLM with JSON mode
            response = await self.llm.generate_json(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent output
            )
            
            # Validate response against schema
            summary_output = MeetingSummaryOutput(**response)
            return summary_output
            
        except LLMResponseParseError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise SummaryGenerationError(f"Failed to parse AI response: {e}")
        except ValidationError as e:
            logger.error(f"LLM response validation failed: {e}")
            raise SummaryGenerationError(f"AI response validation failed: {e}")
        except LLMError as e:
            logger.error(f"LLM API error: {e}")
            raise SummaryGenerationError(f"AI service error: {e}")


async def generate_meeting_summary(db: AsyncSession, meeting_id: int) -> Meeting:
    """
    Convenience function to generate a meeting summary.
    
    Args:
        db: Database session
        meeting_id: ID of the meeting to summarize
        
    Returns:
        Updated Meeting object
    """
    service = MeetingSummaryService(db)
    return await service.generate_summary(meeting_id)

