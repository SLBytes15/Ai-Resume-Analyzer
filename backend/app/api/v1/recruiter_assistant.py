import uuid
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_active_recruiter_context
from app.core.database import get_db
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.schemas.recruiter_assistant import (
    RecruiterConversationCreateRequest,
    RecruiterConversationDetailResponse,
    RecruiterConversationResponse,
    RecruiterConversationUpdateRequest,
    RecruiterMessageCreateRequest,
    RecruiterMessageResponse,
    RecruiterMessageResponsePayload,
)
from app.services.recruiter_conversation_service import (
    create_recruiter_conversation,
    delete_recruiter_conversation,
    get_recruiter_conversation,
    list_recruiter_conversations,
    post_recruiter_message,
    update_recruiter_conversation,
)

router = APIRouter()


@router.post(
    "/conversations",
    response_model=RecruiterConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start an organization-scoped recruiter AI conversation",
)
async def create_conversation(
    payload: RecruiterConversationCreateRequest,
    recruiter_context: Tuple[User, Organization, OrganizationMembership] = Depends(get_active_recruiter_context),
    db: AsyncSession = Depends(get_db),
) -> RecruiterConversationResponse:
    """Initialize a hiring intelligence thread scoped strictly to the recruiter's active organization."""
    user, org, _ = recruiter_context
    conv = await create_recruiter_conversation(
        db=db,
        organization=org,
        user=user,
        payload=payload,
    )
    res = RecruiterConversationResponse.model_validate(conv)
    res.message_count = len(conv.messages) if conv.messages else 0
    if conv.messages:
        res.last_message = RecruiterMessageResponse.model_validate(conv.messages[-1])
    return res


@router.get(
    "/conversations",
    response_model=List[RecruiterConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="List recruiter AI conversations for the active organization",
)
async def list_conversations(
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    recruiter_context: Tuple[User, Organization, OrganizationMembership] = Depends(get_active_recruiter_context),
    db: AsyncSession = Depends(get_db),
) -> List[RecruiterConversationResponse]:
    """Retrieve all conversations belonging to the recruiter's active organization context."""
    _, org, _ = recruiter_context
    conversations = await list_recruiter_conversations(
        db=db,
        organization_id=org.id,
        is_archived=is_archived,
        limit=limit,
        offset=offset,
    )
    items = []
    for c in conversations:
        res = RecruiterConversationResponse.model_validate(c)
        res.message_count = len(c.messages) if c.messages else 0
        if c.messages:
            res.last_message = RecruiterMessageResponse.model_validate(c.messages[-1])
        items.append(res)
    return items


@router.get(
    "/conversations/{conversation_id}",
    response_model=RecruiterConversationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full conversation history and messages",
)
async def get_conversation_detail(
    conversation_id: uuid.UUID = Path(..., description="Conversation UUID"),
    recruiter_context: Tuple[User, Organization, OrganizationMembership] = Depends(get_active_recruiter_context),
    db: AsyncSession = Depends(get_db),
) -> RecruiterConversationDetailResponse:
    """Retrieve complete message thread for an organization-scoped conversation."""
    _, org, _ = recruiter_context
    conv = await get_recruiter_conversation(
        db=db,
        organization_id=org.id,
        conversation_id=conversation_id,
        include_messages=True,
    )
    res = RecruiterConversationDetailResponse.model_validate(conv)
    res.message_count = len(conv.messages) if conv.messages else 0
    return res


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=RecruiterMessageResponsePayload,
    status_code=status.HTTP_201_CREATED,
    summary="Post question to Recruiter AI Assistant and receive grounded response",
)
async def send_message(
    payload: RecruiterMessageCreateRequest,
    conversation_id: uuid.UUID = Path(..., description="Conversation UUID"),
    recruiter_context: Tuple[User, Organization, OrganizationMembership] = Depends(get_active_recruiter_context),
    db: AsyncSession = Depends(get_db),
) -> RecruiterMessageResponsePayload:
    """Send natural-language hiring inquiry; executes safe SQL retrieval and returns grounded answer."""
    user, org, _ = recruiter_context
    user_msg, assistant_msg = await post_recruiter_message(
        db=db,
        organization=org,
        user=user,
        conversation_id=conversation_id,
        payload=payload,
    )
    return RecruiterMessageResponsePayload(
        user_message=RecruiterMessageResponse.model_validate(user_msg),
        assistant_message=RecruiterMessageResponse.model_validate(assistant_msg),
    )


@router.patch(
    "/conversations/{conversation_id}",
    response_model=RecruiterConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update conversation title or archive state",
)
async def update_conversation(
    payload: RecruiterConversationUpdateRequest,
    conversation_id: uuid.UUID = Path(..., description="Conversation UUID"),
    recruiter_context: Tuple[User, Organization, OrganizationMembership] = Depends(get_active_recruiter_context),
    db: AsyncSession = Depends(get_db),
) -> RecruiterConversationResponse:
    """Update title or archive state for an active organization's conversation."""
    _, org, _ = recruiter_context
    conv = await update_recruiter_conversation(
        db=db,
        organization_id=org.id,
        conversation_id=conversation_id,
        payload=payload,
    )
    return RecruiterConversationResponse.model_validate(conv)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation and cascade all its messages",
)
async def delete_conversation(
    conversation_id: uuid.UUID = Path(..., description="Conversation UUID"),
    recruiter_context: Tuple[User, Organization, OrganizationMembership] = Depends(get_active_recruiter_context),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete a conversation and its messages from the active organization."""
    _, org, _ = recruiter_context
    await delete_recruiter_conversation(
        db=db,
        organization_id=org.id,
        conversation_id=conversation_id,
    )
