import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class ConversationPurpose(str, Enum):
    CAREER_GUIDANCE = "CAREER_GUIDANCE"
    ROLE_TRANSITION = "ROLE_TRANSITION"
    SKILL_DEVELOPMENT = "SKILL_DEVELOPMENT"
    INTERVIEW_PREP = "INTERVIEW_PREP"
    RESUME_FEEDBACK = "RESUME_FEEDBACK"
    PROJECT_DISCUSSION = "PROJECT_DISCUSSION"
    RESUME_IMPROVEMENT = "RESUME_IMPROVEMENT"
    GENERAL = "GENERAL"


class MessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class CareerConversation(Base):
    __tablename__ = "career_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_sha256: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    target_role: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    conversation_title: Mapped[str] = mapped_column(
        String(255),
        default="New Conversation",
        nullable=False,
    )
    conversation_type: Mapped[str] = mapped_column(
        String(64),
        default=ConversationPurpose.GENERAL.value,
        nullable=False,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    candidate = relationship("CandidateProfile", back_populates="career_conversations")
    resume = relationship("Resume")
    messages = relationship(
        "CareerMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="CareerMessage.created_at.asc()",
    )

    __table_args__ = (
        Index("idx_career_conversations_candidate_updated", "candidate_id", "updated_at"),
        Index("idx_career_conversations_candidate_archived", "candidate_id", "is_archived"),
    )

    def __repr__(self) -> str:
        return f"<CareerConversation id={self.id} candidate_id={self.candidate_id} title='{self.conversation_title}' type={self.conversation_type}>"


class CareerMessage(Base):
    __tablename__ = "career_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("career_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    context_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    conversation = relationship("CareerConversation", back_populates="messages")

    __table_args__ = (
        Index("idx_career_messages_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CareerMessage id={self.id} role={self.role} conversation_id={self.conversation_id}>"
