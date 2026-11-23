import logging
import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import utc_now
from app.models.candidate import CandidateProfile, Resume
from app.models.career_assistant import (
    CareerConversation,
    CareerMessage,
    ConversationPurpose,
    MessageRole,
)
from app.models.resume_analysis import AnalysisStatus, ResumeAnalysis
from app.schemas.career_assistant import (
    CareerConversationCreateRequest,
    CareerConversationUpdateRequest,
    CareerMessageCreateRequest,
)
from app.services.career_assistant_service import career_assistant_service
from app.services.career_retrieval_service import career_retrieval_service

logger = logging.getLogger(__name__)


async def get_candidate_conversation(
    db: AsyncSession,
    candidate: CandidateProfile,
    conversation_id: uuid.UUID,
    include_messages: bool = False,
) -> CareerConversation:
    """Fetch conversation by ID, strictly enforcing candidate ownership."""
    stmt = select(CareerConversation).where(
        CareerConversation.id == conversation_id,
        CareerConversation.candidate_id == candidate.id,
    )
    if include_messages:
        stmt = stmt.options(selectinload(CareerConversation.messages))

    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career conversation not found",
        )
    return conv


async def create_career_conversation(
    db: AsyncSession,
    candidate: CandidateProfile,
    payload: CareerConversationCreateRequest,
) -> CareerConversation:
    """Initialize a new career conversation, optionally tied to a verified resume version."""
    resume: Optional[Resume] = None
    resume_sha256: Optional[str] = None

    if payload.resume_id:
        stmt = select(Resume).where(
            Resume.id == payload.resume_id,
            Resume.candidate_id == candidate.id,
        )
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected resume not found",
            )
        resume_sha256 = resume.sha256

    # Auto-generate title if not provided
    title = payload.title
    if not title:
        purpose_label = payload.conversation_purpose.value.replace("_", " ").title()
        if payload.target_role:
            title = f"{payload.target_role} — {purpose_label}"
        elif resume:
            title = f"{resume.original_filename} — {purpose_label}"
        else:
            title = f"General Career — {purpose_label}"

    conversation = CareerConversation(
        candidate_id=candidate.id,
        resume_id=resume.id if resume else None,
        resume_sha256=resume_sha256,
        target_role=payload.target_role,
        conversation_title=title[:255],
        conversation_type=payload.conversation_purpose.value,
        is_archived=False,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    # If opening message was provided, process and respond immediately
    if payload.initial_message and payload.initial_message.strip():
        await post_candidate_message(
            db=db,
            candidate=candidate,
            conversation_id=conversation.id,
            payload=CareerMessageCreateRequest(content=payload.initial_message.strip()),
        )
        await db.refresh(conversation)

    return conversation


async def list_career_conversations(
    db: AsyncSession,
    candidate: CandidateProfile,
    is_archived: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[CareerConversation]:
    """List conversations owned by authenticated candidate, ordered by most recently active."""
    stmt = (
        select(CareerConversation)
        .where(CareerConversation.candidate_id == candidate.id)
        .options(selectinload(CareerConversation.messages))
    )
    if is_archived is not None:
        stmt = stmt.where(CareerConversation.is_archived == is_archived)

    stmt = stmt.order_by(CareerConversation.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def post_candidate_message(
    db: AsyncSession,
    candidate: CandidateProfile,
    conversation_id: uuid.UUID,
    payload: CareerMessageCreateRequest,
) -> Tuple[CareerMessage, CareerMessage]:
    """
    Submits user question, performs section-aware context retrieval,
    executes Ollama inference, and persists both messages.
    """
    conv = await get_candidate_conversation(db, candidate, conversation_id, include_messages=True)

    # 1. Fetch attached resume if present
    resume: Optional[Resume] = None
    if conv.resume_id:
        stmt = select(Resume).where(
            Resume.id == conv.resume_id,
            Resume.candidate_id == candidate.id,
        )
        resume = (await db.execute(stmt)).scalar_one_or_none()

    # 2. Fetch latest completed M7 analysis if requested and resume attached
    m7_analysis: Optional[ResumeAnalysis] = None
    if payload.include_m7_analysis and resume:
        m7_stmt = (
            select(ResumeAnalysis)
            .where(
                ResumeAnalysis.resume_id == resume.id,
                ResumeAnalysis.candidate_id == candidate.id,
                ResumeAnalysis.status == AnalysisStatus.COMPLETED.value,
            )
            .order_by(ResumeAnalysis.created_at.desc())
        )
        m7_analysis = (await db.execute(m7_stmt)).scalars().first()

    # 3. Persist User Message
    user_msg = CareerMessage(
        conversation_id=conv.id,
        role=MessageRole.USER.value,
        content=payload.content.strip(),
    )
    db.add(user_msg)
    await db.flush()

    # 4. Section-aware Context Retrieval
    retrieved = career_retrieval_service.retrieve_context(
        query=payload.content,
        resume=resume,
        m7_analysis=m7_analysis,
        conversation_purpose=conv.conversation_type,
        target_role=conv.target_role,
    )

    # 5. Generate Assistant Response
    response_text, model_used, is_fallback = await career_assistant_service.generate_response(
        user_message=payload.content,
        retrieved_context=retrieved,
        history=conv.messages,
        target_role=conv.target_role,
        purpose=conv.conversation_type,
    )

    context_metadata = {
        "resume_id": str(resume.id) if resume else None,
        "resume_sha256": resume.sha256 if resume else None,
        "m7_analysis_id": str(m7_analysis.id) if m7_analysis else None,
        "retrieved_sections": retrieved.retrieved_sections,
        "evidence_snippets": retrieved.evidence_snippets,
        "is_fallback": is_fallback,
    }

    assistant_msg = CareerMessage(
        conversation_id=conv.id,
        role=MessageRole.ASSISTANT.value,
        content=response_text,
        context_metadata=context_metadata,
        model_name=model_used,
    )
    db.add(assistant_msg)

    # Update conversation timestamp
    conv.updated_at = utc_now()

    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)

    return user_msg, assistant_msg


async def update_career_conversation(
    db: AsyncSession,
    candidate: CandidateProfile,
    conversation_id: uuid.UUID,
    payload: CareerConversationUpdateRequest,
) -> CareerConversation:
    """Update title or archive state of a candidate's conversation."""
    conv = await get_candidate_conversation(db, candidate, conversation_id)
    if payload.conversation_title is not None:
        conv.conversation_title = payload.conversation_title.strip()
    if payload.is_archived is not None:
        conv.is_archived = payload.is_archived

    conv.updated_at = utc_now()
    await db.commit()
    await db.refresh(conv)
    return conv


async def delete_career_conversation(
    db: AsyncSession,
    candidate: CandidateProfile,
    conversation_id: uuid.UUID,
) -> None:
    """Delete conversation and cascade delete its messages."""
    conv = await get_candidate_conversation(db, candidate, conversation_id)
    await db.delete(conv)
    await db.commit()
