"""
Meetings API Endpoints

This module defines the API endpoints for meeting management.
Includes full CRUD operations, AI summary generation, and action item extraction.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.action_item import ActionItem
from app.models.meeting import Meeting, MeetingStatus
from app.schemas.action_item import ActionItemResponse
from app.schemas.meeting import (
    MeetingCreate,
    MeetingListResponse,
    MeetingResponse,
    MeetingUpdate,
)
from app.services.action_item_service import (
    ActionItemExtractionError,
    ActionItemExtractionService,
    MeetingNotFoundError as ActionItemMeetingNotFoundError,
)
from app.services.summary_service import (
    MeetingNotFoundError,
    MeetingSummaryService,
    SummaryGenerationError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[MeetingListResponse])
async def list_meetings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    status_filter: Optional[MeetingStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all meetings with pagination.

    Returns a list of meetings ordered by creation time (newest first).
    Use skip and limit parameters for pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 20, max: 100)
    - **status_filter**: Optional status filter (draft/processing/completed)
    """
    # Build query
    query = select(Meeting)
    
    # Apply status filter if provided
    if status_filter:
        query = query.where(Meeting.status == status_filter.value)
    
    # Order by created_at descending (newest first)
    query = query.order_by(desc(Meeting.created_at))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    meetings = result.scalars().all()
    
    # Build response with action_item_count
    response = []
    for meeting in meetings:
        response.append(
            MeetingListResponse(
                id=meeting.id,
                title=meeting.title,
                start_time=meeting.start_time,
                status=meeting.status,
                created_at=meeting.created_at,
                action_item_count=len(meeting.action_items),
            )
        )
    
    return response


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting: MeetingCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new meeting.

    Creates a new meeting record with the provided information.
    The meeting is created with status 'draft' by default.
    
    - **title**: Meeting title (required)
    - **start_time**: Meeting start time (optional)
    - **end_time**: Meeting end time (optional)
    - **original_text**: Original meeting content/transcript (optional)
    """
    # Create new meeting instance
    db_meeting = Meeting(
        title=meeting.title,
        start_time=meeting.start_time,
        end_time=meeting.end_time,
        original_text=meeting.original_text,
        participants=meeting.participants,
        status=MeetingStatus.DRAFT.value,
    )
    
    # Add to database
    db.add(db_meeting)
    await db.flush()
    await db.refresh(db_meeting)
    
    logger.info(f"Created meeting: id={db_meeting.id}, title='{db_meeting.title}'")
    
    return db_meeting


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a meeting by ID.

    Returns the full meeting details including summary, structured fields,
    and action items.
    
    - **meeting_id**: The ID of the meeting to retrieve
    """
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with id {meeting_id} not found",
        )
    
    return meeting


@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: int,
    meeting_update: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a meeting.

    Updates the meeting with the provided information.
    Only provided fields will be updated.
    
    - **meeting_id**: The ID of the meeting to update
    """
    # Get existing meeting
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with id {meeting_id} not found",
        )
    
    # Update only provided fields
    update_data = meeting_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value is not None:
            setattr(meeting, field, value.value if hasattr(value, "value") else value)
        else:
            setattr(meeting, field, value)
    
    await db.flush()
    await db.refresh(meeting)
    
    logger.info(f"Updated meeting: id={meeting.id}")
    
    return meeting


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a meeting.

    Deletes the meeting and all associated action items (cascade delete).
    
    - **meeting_id**: The ID of the meeting to delete
    """
    # Get existing meeting
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with id {meeting_id} not found",
        )
    
    # Delete meeting (action items are cascade deleted)
    await db.delete(meeting)
    await db.flush()
    
    logger.info(f"Deleted meeting: id={meeting_id}")
    
    return None


@router.post("/{meeting_id}/generate-summary", response_model=MeetingResponse)
async def generate_meeting_summary(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate AI summary for a meeting.

    Triggers AI processing to generate a structured summary from the meeting content.
    The meeting must have original_text content to generate a summary.
    
    The generated summary includes:
    - **summary**: A concise 3-5 sentence overview
    - **topics**: List of core topics discussed
    - **decisions**: List of decisions made
    - **discussion_points**: Key discussion points and viewpoints
    
    - **meeting_id**: The ID of the meeting to summarize
    """
    try:
        # Create summary service and generate summary
        summary_service = MeetingSummaryService(db)
        meeting = await summary_service.generate_summary(meeting_id)
        
        # Refresh to get updated data
        await db.refresh(meeting)
        
        return meeting
        
    except MeetingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with id {meeting_id} not found",
        )
    except SummaryGenerationError as e:
        logger.error(f"Summary generation failed for meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{meeting_id}/summary-status")
async def get_summary_status(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the summary generation status of a meeting.

    Returns the current processing status of the meeting.
    
    - **meeting_id**: The ID of the meeting to check
    
    Returns:
    - **status**: Current status (draft/processing/completed)
    - **has_summary**: Whether the meeting has a generated summary
    """
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with id {meeting_id} not found",
        )
    
    return {
        "meeting_id": meeting.id,
        "status": meeting.status,
        "has_summary": meeting.summary is not None,
        "has_content": meeting.original_text is not None and len(meeting.original_text.strip()) > 0,
    }


@router.post(
    "/{meeting_id}/extract-actions",
    response_model=List[ActionItemResponse],
)
async def extract_meeting_action_items(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Extract action items from meeting content using AI.

    Analyzes the meeting content and automatically extracts actionable tasks.
    Each action item includes:
    - **title**: Concise action description
    - **owner**: Responsible person (if identified)
    - **due_date**: Deadline (if mentioned)
    - **priority**: Assessed priority (high/medium/low)
    
    The meeting must have original_text content to extract action items.
    
    - **meeting_id**: The ID of the meeting to extract action items from
    """
    try:
        # Create extraction service and extract action items
        service = ActionItemExtractionService(db)
        action_items = await service.extract_action_items(meeting_id)
        
        return action_items
        
    except ActionItemMeetingNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with id {meeting_id} not found",
        )
    except ActionItemExtractionError as e:
        logger.error(f"Action item extraction failed for meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{meeting_id}/action-items",
    response_model=List[ActionItemResponse],
)
async def get_meeting_action_items(
    meeting_id: int,
    status_filter: Optional[str] = Query(
        None, 
        description="Filter by status (todo/in_progress/done/cancelled)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all action items for a meeting.

    Returns all action items associated with the specified meeting.
    Optionally filter by status.
    
    - **meeting_id**: The ID of the meeting
    - **status_filter**: Optional status filter (todo/in_progress/done/cancelled)
    """
    # Verify meeting exists
    meeting_result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    if not meeting_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting with id {meeting_id} not found",
        )
    
    # Build query for action items
    query = select(ActionItem).where(ActionItem.meeting_id == meeting_id)
    
    # Apply status filter if provided
    if status_filter:
        query = query.where(ActionItem.status == status_filter)
    
    # Order by created_at descending
    query = query.order_by(desc(ActionItem.created_at))
    
    # Execute query
    result = await db.execute(query)
    action_items = result.scalars().all()
    
    return action_items
