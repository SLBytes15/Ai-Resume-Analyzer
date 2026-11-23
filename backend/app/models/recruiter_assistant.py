import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class RecruiterConversationType(str, Enum):
    GENERAL_HIRING = "GENERAL_HIRING"
    JOB_ANALYSIS = "JOB_ANALYSIS"
    APPLICANT_SCREENING = "APPLICANT_SCREENING"
    CANDIDATE_COMPARISON = "CANDIDATE_COMPARISON"
    PIPELINE_METRICS = "PIPELINE_METRICS"


class RecruiterMessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


class RecruiterConversation(Base):
    __tablename__ = "recruiter_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_title: Mapped[str] = mapped_column(
        String(255),
        default="Hiring Intelligence Chat",
        nullable=False,
    )
    conversation_type: Mapped[str] = mapped_column(
        String(64),
        default=RecruiterConversationType.GENERAL_HIRING.value,
        nullable=False,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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
    organization: Mapped["Organization"] = relationship("Organization")
    created_by: Mapped["User"] = relationship("User")
    messages: Mapped[List["RecruiterMessage"]] = relationship(
        "RecruiterMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="RecruiterMessage.created_at",
    )

    __table_args__ = (
        Index("idx_recruiter_conv_org_updated", "organization_id", "updated_at"),
        Index("idx_recruiter_conv_org_archived", "organization_id", "is_archived"),
    )


class RecruiterMessage(Base):
    __tablename__ = "recruiter_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recruiter_conversations.id", ondelete="CASCADE"),
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

    # Relationship
    conversation: Mapped["RecruiterConversation"] = relationship(
        "RecruiterConversation",
        back_populates="messages",
    )

    __table_args__ = (
        Index("idx_recruiter_msg_conv_created", "conversation_id", "created_at"),
    )
