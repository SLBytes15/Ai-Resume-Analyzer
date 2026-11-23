import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.career_assistant import (
    CareerConversationCreateRequest,
    CareerConversationDetailResponse,
    CareerConversationResponse,
    CareerConversationUpdateRequest,
    CareerMessageCreateRequest,
    CareerMessageResponse,
    CareerMessageResponsePayload,
)
from app.services.career_conversation_service import (
    create_career_conversation,
    delete_career_conversation,
    get_candidate_conversation,
    list_career_conversations,
    post_candidate_message,
    update_career_conversation,
)
from app.services.resume_service import get_or_create_candidate_profile

router = APIRouter()


@router.post(
    "/conversations",
    response_model=CareerConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new Career Assistant conversation",
)
async def create_conversation(
    payload: CareerConversationCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CareerConversationResponse:
    """Initialize a conversational career guidance thread with optional resume grounding."""
    candidate = await get_or_create_candidate_profile(db, current_user)
    conv = await create_career_conversation(
        db=db,
        candidate=candidate,
        payload=payload,
    )
    return CareerConversationResponse.model_validate(conv)


@router.get(
    "/conversations",
    response_model=List[CareerConversationResponse],
    status_code=status.HTTP_200_OK,
    summary="List candidate's career conversations",
)
async def list_conversations(
    is_archived: Optional[bool] = Query(None, description="Filter by archived state"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[CareerConversationResponse]:
    """Retrieve all conversational threads belonging to the authenticated candidate."""
    candidate = await get_or_create_candidate_profile(db, current_user)
    conversations = await list_career_conversations(
        db=db,
        candidate=candidate,
        is_archived=is_archived,
        limit=limit,
        offset=offset,
    )

    items = []
    for c in conversations:
        res = CareerConversationResponse.model_validate(c)
        res.message_count = len(c.messages) if c.messages else 0
        if c.messages:
            res.last_message = CareerMessageResponse.model_validate(c.messages[-1])
        items.append(res)

    return items


@router.get(
    "/conversations/{conversation_id}",
    response_model=CareerConversationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full conversation history and details",
)
async def get_conversation_detail(
    conversation_id: uuid.UUID = Path(..., description="Conversation UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CareerConversationDetailResponse:
    """Retrieve complete message thread for a candidate's conversation."""
    candidate = await get_or_create_candidate_profile(db, current_user)
    conv = await get_candidate_conversation(
        db=db,
        candidate=candidate,
        conversation_id=conversation_id,
        include_messages=True,
    )
    res = CareerConversationDetailResponse.model_validate(conv)
    res.message_count = len(conv.messages) if conv.messages else 0
    return res


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=CareerMessageResponsePayload,
    status_code=status.HTTP_201_CREATED,
    summary="Post a message and receive assistant guidance",
)
async def post_message(
    conversation_id: uuid.UUID = Path(..., description="Conversation UUID"),
    payload: CareerMessageCreateRequest = ...,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CareerMessageResponsePayload:
    """
    Submit a message to the conversational assistant.
    Retrieves section-aware context from candidate's resume and M7 findings,
    executes Ollama inference, and returns both user and assistant messages.
    """
    candidate = await get_or_create_candidate_profile(db, current_user)
    user_msg, assistant_msg = await post_candidate_message(
        db=db,
        candidate=candidate,
        conversation_id=conversation_id,
        payload=payload,
    )
    return CareerMessageResponsePayload(
        user_message=CareerMessageResponse.model_validate(user_msg),
        assistant_message=CareerMessageResponse.model_validate(assistant_msg),
    )


@router.patch(
    "/conversations/{conversation_id}",
    response_model=CareerConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update conversation title or archive status",
)
async def update_conversation(
    conversation_id: uuid.UUID = Path(..., description="Conversation UUID"),
    payload: CareerConversationUpdateRequest = ...,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CareerConversationResponse:
    """Update title or archive state."""
    candidate = await get_or_create_candidate_profile(db, current_user)
    conv = await update_career_conversation(
        db=db,
        candidate=candidate,
        conversation_id=conversation_id,
        payload=payload,
    )
    return CareerConversationResponse.model_validate(conv)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
)
async def delete_conversation(
    conversation_id: uuid.UUID = Path(..., description="Conversation UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and its message history."""
    candidate = await get_or_create_candidate_profile(db, current_user)
    await delete_career_conversation(
        db=db,
        candidate=candidate,
        conversation_id=conversation_id,
    )
    return None
