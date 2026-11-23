import logging
import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import utc_now
from app.models.organization import Organization
from app.models.recruiter_assistant import (
    RecruiterConversation,
    RecruiterConversationType,
    RecruiterMessage,
    RecruiterMessageRole,
)
from app.models.user import User
from app.schemas.recruiter_assistant import (
    RecruiterConversationCreateRequest,
    RecruiterConversationUpdateRequest,
    RecruiterMessageCreateRequest,
)
from app.services.recruiter_assistant_service import recruiter_assistant_service
from app.services.recruiter_retrieval_service import recruiter_retrieval_service

logger = logging.getLogger(__name__)


async def get_recruiter_conversation(
    db: AsyncSession,
    organization_id: uuid.UUID,
    conversation_id: uuid.UUID,
    include_messages: bool = False,
) -> RecruiterConversation:
    """Fetch conversation by ID, strictly enforcing organization tenant isolation."""
    stmt = select(RecruiterConversation).where(
        RecruiterConversation.id == conversation_id,
        RecruiterConversation.organization_id == organization_id,
    )
    if include_messages:
        stmt = stmt.options(selectinload(RecruiterConversation.messages))

    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recruiter conversation not found in this organization context",
        )
    return conv


async def list_recruiter_conversations(
    db: AsyncSession,
    organization_id: uuid.UUID,
    is_archived: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[RecruiterConversation]:
    """Retrieve all conversations for the organization ordered by last update."""
    stmt = (
        select(RecruiterConversation)
        .options(selectinload(RecruiterConversation.messages))
        .where(RecruiterConversation.organization_id == organization_id)
    )
    if is_archived is not None:
        stmt = stmt.where(RecruiterConversation.is_archived == is_archived)

    stmt = stmt.order_by(desc(RecruiterConversation.updated_at)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_recruiter_conversation(
    db: AsyncSession,
    organization: Organization,
    user: User,
    payload: RecruiterConversationCreateRequest,
) -> RecruiterConversation:
    """Initialize a new organization-scoped recruiter conversation."""
    title = payload.conversation_title
    if not title:
        title = f"Hiring Intelligence — {payload.conversation_type.value.replace('_', ' ').title()}"

    conversation = RecruiterConversation(
        organization_id=organization.id,
        created_by_user_id=user.id,
        conversation_title=title[:255],
        conversation_type=payload.conversation_type.value,
        is_archived=False,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    # Process initial question if provided
    if payload.initial_message and payload.initial_message.strip():
        user_msg = RecruiterMessage(
            conversation_id=conversation.id,
            role=RecruiterMessageRole.USER.value,
            content=payload.initial_message.strip(),
            created_at=utc_now(),
        )
        db.add(user_msg)

        retrieved = await recruiter_retrieval_service.retrieve_context(
            db=db,
            organization_id=organization.id,
            query=payload.initial_message.strip(),
        )

        reply, model_name, is_fallback = await recruiter_assistant_service.generate_response(
            user_message=payload.initial_message.strip(),
            organization_name=organization.name,
            retrieved_context=retrieved,
            history=[],
        )

        meta = {
            "organization_id": str(organization.id),
            "intent": retrieved.intent.value,
            "retrieved_job_ids": retrieved.retrieved_job_ids,
            "retrieved_app_ids": retrieved.retrieved_app_ids,
            "screening_run_ids": retrieved.screening_run_ids,
            "sources_used": retrieved.sources_used,
            "evidence_snippets": retrieved.evidence_snippets,
            "is_fallback": is_fallback,
        }

        assistant_msg = RecruiterMessage(
            conversation_id=conversation.id,
            role=RecruiterMessageRole.ASSISTANT.value,
            content=reply,
            context_metadata=meta,
            model_name=model_name,
            created_at=utc_now(),
        )
        db.add(assistant_msg)
        conversation.updated_at = utc_now()
        await db.commit()

    return await get_recruiter_conversation(
        db=db,
        organization_id=organization.id,
        conversation_id=conversation.id,
        include_messages=True,
    )


async def post_recruiter_message(
    db: AsyncSession,
    organization: Organization,
    user: User,
    conversation_id: uuid.UUID,
    payload: RecruiterMessageCreateRequest,
) -> Tuple[RecruiterMessage, RecruiterMessage]:
    """Post recruiter message and generate grounded assistant response with full context provenance."""
    conv = await get_recruiter_conversation(
        db=db,
        organization_id=organization.id,
        conversation_id=conversation_id,
        include_messages=True,
    )

    user_msg = RecruiterMessage(
        conversation_id=conv.id,
        role=RecruiterMessageRole.USER.value,
        content=payload.content.strip(),
        created_at=utc_now(),
    )
    db.add(user_msg)

    # 1. Allowlisted Intent-Driven SQL Retrieval
    retrieved = await recruiter_retrieval_service.retrieve_context(
        db=db,
        organization_id=organization.id,
        query=payload.content.strip(),
        job_id=payload.job_id,
        application_id=payload.application_id,
    )

    # 2. Ollama / Fallback Response Generation
    reply, model_name, is_fallback = await recruiter_assistant_service.generate_response(
        user_message=payload.content.strip(),
        organization_name=organization.name,
        retrieved_context=retrieved,
        history=conv.messages,
    )

    meta = {
        "organization_id": str(organization.id),
        "intent": retrieved.intent.value,
        "retrieved_job_ids": retrieved.retrieved_job_ids,
        "retrieved_app_ids": retrieved.retrieved_app_ids,
        "screening_run_ids": retrieved.screening_run_ids,
        "sources_used": retrieved.sources_used,
        "evidence_snippets": retrieved.evidence_snippets,
        "is_fallback": is_fallback,
    }

    assistant_msg = RecruiterMessage(
        conversation_id=conv.id,
        role=RecruiterMessageRole.ASSISTANT.value,
        content=reply,
        context_metadata=meta,
        model_name=model_name,
        created_at=utc_now(),
    )
    db.add(assistant_msg)

    conv.updated_at = utc_now()
    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)

    return user_msg, assistant_msg


async def update_recruiter_conversation(
    db: AsyncSession,
    organization_id: uuid.UUID,
    conversation_id: uuid.UUID,
    payload: RecruiterConversationUpdateRequest,
) -> RecruiterConversation:
    """Rename or archive conversation."""
    conv = await get_recruiter_conversation(
        db=db,
        organization_id=organization_id,
        conversation_id=conversation_id,
    )
    if payload.conversation_title is not None:
        conv.conversation_title = payload.conversation_title.strip()[:255]
    if payload.is_archived is not None:
        conv.is_archived = payload.is_archived

    conv.updated_at = utc_now()
    await db.commit()
    return await get_recruiter_conversation(
        db=db,
        organization_id=organization_id,
        conversation_id=conversation_id,
        include_messages=True,
    )


async def delete_recruiter_conversation(
    db: AsyncSession,
    organization_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> None:
    """Delete conversation and all its messages (cascades)."""
    conv = await get_recruiter_conversation(
        db=db,
        organization_id=organization_id,
        conversation_id=conversation_id,
    )
    await db.delete(conv)
    await db.commit()
