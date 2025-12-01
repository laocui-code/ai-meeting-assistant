"""
Action Items API Endpoints

This module defines the API endpoints for action item management.
Implemented in E05: CRUD operations, status transitions, and batch updates.
"""

# E05：行动事项管理接口，标记本文件为 E05 迭代范围

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.action_item import ActionItem
from app.schemas.action_item import (
    ActionItemCreate,
    ActionItemResponse,
    ActionItemStatusUpdate,
    ActionItemUpdate,
    BatchResponse,
    BatchStatusUpdate,
)
from app.services.action_item_service import (
    ActionItemManagementService,
    ActionItemNotFoundError,
    InvalidStatusTransitionError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# E05：辅助函数 - 统一的404错误处理
# =============================================================================


async def get_action_item_or_404(
    db: AsyncSession, action_item_id: int
) -> ActionItem:
    """
    E05: Get action item or raise 404.
    
    Args:
        db: Database session
        action_item_id: ID of the action item
        
    Returns:
        ActionItem object
        
    Raises:
        HTTPException: 404 if not found
    """
    service = ActionItemManagementService(db)
    try:
        return await service.get_action_item(action_item_id)
    except ActionItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item {action_item_id} not found",
        )


# =============================================================================
# E05：列表查询与创建接口
# =============================================================================


@router.get("", response_model=List[ActionItemResponse])
async def list_action_items(
    meeting_id: Optional[int] = Query(None, description="Filter by meeting ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    include_deleted: bool = Query(False, description="Include soft-deleted items"),
    db: AsyncSession = Depends(get_db),
):
    """
    E05: List action items.

    Returns all action items, optionally filtered by meeting_id and/or status.
    Soft-deleted items are excluded by default.
    """
    query = select(ActionItem)
    
    # E05：应用过滤条件
    if not include_deleted:
        query = query.where(ActionItem.is_deleted == False)
    
    if meeting_id is not None:
        query = query.where(ActionItem.meeting_id == meeting_id)
    
    if status_filter is not None:
        query = query.where(ActionItem.status == status_filter)
    
    # E05：按创建时间倒序排列
    query = query.order_by(ActionItem.created_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ActionItemResponse, status_code=status.HTTP_201_CREATED)
async def create_action_item(
    action_item: ActionItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    E05: Create a new action item.

    Creates a new action item associated with a meeting.
    """
    # E05：验证关联的会议是否存在
    from app.models.meeting import Meeting
    
    meeting_result = await db.execute(
        select(Meeting).where(Meeting.id == action_item.meeting_id)
    )
    if not meeting_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting {action_item.meeting_id} not found",
        )
    
    # E05：创建行动事项记录
    db_item = ActionItem(
        meeting_id=action_item.meeting_id,
        title=action_item.title,
        description=action_item.description,
        owner=action_item.owner,
        due_date=action_item.due_date,
        priority=action_item.priority.value if action_item.priority else "medium",
        status="todo",
    )
    
    db.add(db_item)
    await db.flush()
    await db.refresh(db_item)
    
    logger.info(f"Created action item {db_item.id} for meeting {action_item.meeting_id}")
    
    return db_item


# =============================================================================
# E05：单个事项的增删改查接口
# =============================================================================


@router.get("/{action_item_id}", response_model=ActionItemResponse)
async def get_action_item(
    action_item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    E05: Get an action item by ID.

    Returns the full action item details.
    Soft-deleted items are not returned (404).
    """
    return await get_action_item_or_404(db, action_item_id)


@router.put("/{action_item_id}", response_model=ActionItemResponse)
async def update_action_item(
    action_item_id: int,
    action_item: ActionItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    E05: Update an action item.

    Updates the action item with the provided information.
    Only provided fields are updated (partial update).
    Status transitions are validated.
    """
    service = ActionItemManagementService(db)
    
    try:
        updated_item = await service.update_action_item(action_item_id, action_item)
        return updated_item
    except ActionItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item {action_item_id} not found",
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch("/{action_item_id}/status", response_model=ActionItemResponse)
async def update_action_item_status(
    action_item_id: int,
    status_update: ActionItemStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    E05: Update action item status.

    Updates only the status of an action item.
    Validates that the status transition is allowed.
    """
    service = ActionItemManagementService(db)
    
    try:
        updated_item = await service.update_status(action_item_id, status_update.status)
        return updated_item
    except ActionItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item {action_item_id} not found",
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{action_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_item(
    action_item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    E05: Delete an action item.

    Performs a soft delete - the item is marked as deleted but not removed.
    """
    service = ActionItemManagementService(db)
    
    try:
        await service.delete_action_item(action_item_id)
    except ActionItemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action item {action_item_id} not found",
        )


# =============================================================================
# E05：批量操作接口
# =============================================================================


@router.patch("/batch/status", response_model=BatchResponse)
async def batch_update_status(
    batch_data: BatchStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    E05: Batch update status for multiple action items.

    Updates the status of multiple action items in a single operation.
    Uses a single database query for efficiency.
    
    Note: Status transition validation is not performed for each item
    individually. Use with caution.
    
    Returns the count of items actually updated (may be less than
    requested if some IDs don't exist or are already deleted).
    """
    service = ActionItemManagementService(db)
    
    updated_count = await service.batch_update_status(
        ids=batch_data.ids,
        new_status=batch_data.status,
    )
    
    return BatchResponse(
        updated_count=updated_count,
        ids=batch_data.ids,
        message=f"Updated {updated_count} action items to status '{batch_data.status.value}'",
    )
