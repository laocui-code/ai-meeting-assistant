"""
Action Item Service

This module provides the service layer for action item operations:
1. Extraction: Extract action items from meeting content using AI (E04)
2. Management: CRUD operations, status transitions, batch updates (E05)
"""

# E05：行动事项管理服务，涵盖增删改查、状态流转与批量操作

import logging
from datetime import date, datetime
from typing import List, Optional

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_item import ActionItem, ActionItemStatus
from app.models.meeting import Meeting
from app.schemas.action_item import ActionItemUpdate
from app.services.llm_service import (
    LLMError,
    LLMResponseParseError,
    get_llm_service,
)
from app.services.prompts import (
    ActionItemsExtractionOutput,
    build_action_items_prompt,
)

logger = logging.getLogger(__name__)


class ActionItemExtractionError(Exception):
    """Raised when action item extraction fails."""
    pass


class MeetingNotFoundError(Exception):
    """Raised when meeting is not found."""
    pass


class ActionItemNotFoundError(Exception):
    """E05: Raised when action item is not found."""
    pass


class InvalidStatusTransitionError(Exception):
    """E05: Raised when an invalid status transition is attempted."""
    pass


class ActionItemExtractionService:
    """
    Service for extracting action items from meeting content using AI.
    
    This service handles the complete flow of:
    1. Loading meeting from database
    2. Building prompts with meeting content
    3. Calling LLM for action item extraction
    4. Parsing and validating the response
    5. Storing results back to database
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the extraction service.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.llm = get_llm_service()
    
    async def extract_action_items(self, meeting_id: int) -> List[ActionItem]:
        """
        Extract action items from a meeting's content.
        
        This is the main entry point for action item extraction. It:
        1. Loads the meeting from database
        2. Validates that it has content to extract from
        3. Calls LLM to extract action items
        4. Saves extracted items to database
        
        Args:
            meeting_id: ID of the meeting to extract action items from
            
        Returns:
            List of created ActionItem objects
            
        Raises:
            MeetingNotFoundError: If meeting doesn't exist
            ActionItemExtractionError: If extraction fails
        """
        # Load meeting
        meeting = await self._get_meeting(meeting_id)
        if not meeting:
            raise MeetingNotFoundError(f"Meeting with id {meeting_id} not found")
        
        # Validate content exists
        if not meeting.original_text or not meeting.original_text.strip():
            raise ActionItemExtractionError(
                "Meeting has no content to extract action items from. "
                "Please add original_text first."
            )
        
        try:
            # Extract action items using LLM
            extraction_output = await self._extract_from_llm(meeting)
            
            # Save to database
            action_items = await self._save_action_items(
                meeting_id, extraction_output.action_items
            )
            
            logger.info(
                f"Successfully extracted {len(action_items)} action items "
                f"for meeting {meeting_id}"
            )
            
            return action_items
            
        except Exception as e:
            logger.error(f"Failed to extract action items for meeting {meeting_id}: {e}")
            raise ActionItemExtractionError(f"Action item extraction failed: {e}")
    
    async def _get_meeting(self, meeting_id: int) -> Optional[Meeting]:
        """Load a meeting from the database."""
        result = await self.db.execute(
            select(Meeting).where(Meeting.id == meeting_id)
        )
        return result.scalar_one_or_none()
    
    async def _extract_from_llm(self, meeting: Meeting) -> ActionItemsExtractionOutput:
        """
        Extract action items using LLM.
        
        Args:
            meeting: Meeting object with content
            
        Returns:
            Validated ActionItemsExtractionOutput object
            
        Raises:
            ActionItemExtractionError: If LLM call or parsing fails
        """
        # Determine meeting date for relative time conversion
        meeting_date: Optional[date] = None
        if meeting.start_time:
            meeting_date = meeting.start_time.date()
        
        # Build prompt messages
        messages = build_action_items_prompt(
            meeting_content=meeting.original_text,
            participants=meeting.participants,
            meeting_date=meeting_date,
        )
        
        try:
            # Call LLM with JSON mode
            response = await self.llm.generate_json(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent output
            )
            
            # Validate response against schema
            extraction_output = ActionItemsExtractionOutput(**response)
            return extraction_output
            
        except LLMResponseParseError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ActionItemExtractionError(f"Failed to parse AI response: {e}")
        except ValidationError as e:
            logger.error(f"LLM response validation failed: {e}")
            raise ActionItemExtractionError(f"AI response validation failed: {e}")
        except LLMError as e:
            logger.error(f"LLM API error: {e}")
            raise ActionItemExtractionError(f"AI service error: {e}")
    
    async def _save_action_items(
        self,
        meeting_id: int,
        items: List,
    ) -> List[ActionItem]:
        """
        Save extracted action items to database.
        
        Args:
            meeting_id: ID of the parent meeting
            items: List of ActionItemOutput objects from LLM
            
        Returns:
            List of created ActionItem database objects
        """
        action_items = []
        
        for item in items:
            # Parse due_date if provided
            due_date: Optional[datetime] = None
            if item.due_date:
                try:
                    due_date = datetime.strptime(item.due_date, "%Y-%m-%d")
                except ValueError:
                    logger.warning(
                        f"Invalid due_date format '{item.due_date}', setting to None"
                    )
            
            # Create ActionItem record
            db_item = ActionItem(
                meeting_id=meeting_id,
                title=item.title,
                description=item.description or "",
                owner=item.owner,
                due_date=due_date,
                priority=item.priority,
                status="todo",  # Initial status
            )
            self.db.add(db_item)
            action_items.append(db_item)
        
        # Flush to get IDs assigned
        await self.db.flush()
        
        # Refresh all items to get complete data
        for item in action_items:
            await self.db.refresh(item)
        
        logger.info(
            f"Saved {len(action_items)} action items for meeting {meeting_id}"
        )
        
        return action_items


async def extract_meeting_action_items(
    db: AsyncSession, 
    meeting_id: int
) -> List[ActionItem]:
    """
    Convenience function to extract action items from a meeting.
    
    Args:
        db: Database session
        meeting_id: ID of the meeting to extract from
        
    Returns:
        List of created ActionItem objects
    """
    service = ActionItemExtractionService(db)
    return await service.extract_action_items(meeting_id)


# =============================================================================
# E05：行动事项管理服务核心逻辑
# =============================================================================


class ActionItemManagementService:
    """
    E05: Service for managing action items (E05 implementation).
    
    Provides CRUD operations, status transitions with validation,
    soft delete, and batch operations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        E05: Initialize the management service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def get_action_item(self, action_item_id: int) -> ActionItem:
        """
        E05: Get a single action item by ID.
        
        Excludes soft-deleted items.
        
        Args:
            action_item_id: ID of the action item
            
        Returns:
            ActionItem object
            
        Raises:
            ActionItemNotFoundError: If item doesn't exist or is deleted
        """
        result = await self.db.execute(
            select(ActionItem)
            .where(ActionItem.id == action_item_id)
            .where(ActionItem.is_deleted == False)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            raise ActionItemNotFoundError(
                f"Action item with id {action_item_id} not found"
            )
        
        return item
    
    async def update_action_item(
        self,
        action_item_id: int,
        update_data: ActionItemUpdate,
    ) -> ActionItem:
        """
        E05: Update an action item with partial data.
        
        Only updates fields that are explicitly provided (not None).
        Status updates are validated for valid transitions.
        
        Args:
            action_item_id: ID of the action item
            update_data: Pydantic schema with update fields
            
        Returns:
            Updated ActionItem object
            
        Raises:
            ActionItemNotFoundError: If item doesn't exist
            InvalidStatusTransitionError: If status transition is invalid
        """
        # Get existing item
        item = await self.get_action_item(action_item_id)
        
        # E05：获取需要更新的字段（仅包含明确设置的字段）
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # E05：处理状态更新并验证状态流转规则
        if "status" in update_dict:
            new_status = update_dict["status"]
            if isinstance(new_status, str):
                new_status_value = new_status
            else:
                new_status_value = new_status.value
            
            if not ActionItemStatus.is_valid_transition(item.status, new_status_value):
                raise InvalidStatusTransitionError(
                    f"Invalid status transition: {item.status} -> {new_status_value}"
                )
            
            # E05：记录状态变更时间
            update_dict["status_changed_at"] = datetime.utcnow()
            update_dict["status"] = new_status_value
        
        # E05：处理优先级枚举值
        if "priority" in update_dict and update_dict["priority"] is not None:
            priority = update_dict["priority"]
            if hasattr(priority, "value"):
                update_dict["priority"] = priority.value
        
        # E05：应用所有更新
        for field, value in update_dict.items():
            setattr(item, field, value)
        
        item.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(item)
        
        logger.info(f"Updated action item {action_item_id}: {list(update_dict.keys())}")
        
        return item
    
    async def update_status(
        self,
        action_item_id: int,
        new_status: ActionItemStatus,
    ) -> ActionItem:
        """
        E05: Update only the status of an action item.
        
        Validates the status transition before applying.
        
        Args:
            action_item_id: ID of the action item
            new_status: New status to set
            
        Returns:
            Updated ActionItem object
            
        Raises:
            ActionItemNotFoundError: If item doesn't exist
            InvalidStatusTransitionError: If transition is invalid
        """
        item = await self.get_action_item(action_item_id)
        
        new_status_value = new_status.value if hasattr(new_status, "value") else new_status
        
        # E05：验证状态流转是否合法
        if not ActionItemStatus.is_valid_transition(item.status, new_status_value):
            raise InvalidStatusTransitionError(
                f"Invalid status transition: {item.status} -> {new_status_value}"
            )
        
        old_status = item.status
        item.status = new_status_value
        item.status_changed_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(item)
        
        logger.info(
            f"Status change for action item {action_item_id}: "
            f"{old_status} -> {new_status_value}"
        )
        
        return item
    
    async def delete_action_item(self, action_item_id: int) -> None:
        """
        E05: Soft delete an action item.
        
        Sets is_deleted=True and records deleted_at timestamp.
        
        Args:
            action_item_id: ID of the action item
            
        Raises:
            ActionItemNotFoundError: If item doesn't exist
        """
        item = await self.get_action_item(action_item_id)
        
        item.is_deleted = True
        item.deleted_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        
        await self.db.flush()
        
        logger.info(f"Soft deleted action item {action_item_id}")
    
    async def batch_update_status(
        self,
        ids: List[int],
        new_status: ActionItemStatus,
    ) -> int:
        """
        E05: Batch update status for multiple action items.
        
        Uses a single UPDATE query for efficiency.
        All-or-nothing transaction semantics.
        
        Note: This method does NOT validate transitions for each item
        individually for performance reasons. Use with caution.
        
        Args:
            ids: List of action item IDs to update
            new_status: New status to set for all items
            
        Returns:
            Number of items updated
        """
        new_status_value = new_status.value if hasattr(new_status, "value") else new_status
        
        # E05：使用单个UPDATE查询批量更新，提高性能
        result = await self.db.execute(
            update(ActionItem)
            .where(ActionItem.id.in_(ids))
            .where(ActionItem.is_deleted == False)
            .values(
                status=new_status_value,
                status_changed_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        
        updated_count = result.rowcount
        
        logger.info(
            f"Batch status update: {updated_count} items updated to '{new_status_value}'"
        )
        
        return updated_count


# =============================================================================
# E05：便捷方法 - 行动事项管理入口函数
# =============================================================================

async def get_action_item(db: AsyncSession, action_item_id: int) -> ActionItem:
    """E05: Get a single action item by ID."""
    service = ActionItemManagementService(db)
    return await service.get_action_item(action_item_id)


async def update_action_item(
    db: AsyncSession,
    action_item_id: int,
    update_data: ActionItemUpdate,
) -> ActionItem:
    """E05: Update an action item."""
    service = ActionItemManagementService(db)
    return await service.update_action_item(action_item_id, update_data)


async def delete_action_item(db: AsyncSession, action_item_id: int) -> None:
    """E05: Soft delete an action item."""
    service = ActionItemManagementService(db)
    await service.delete_action_item(action_item_id)

