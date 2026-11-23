import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

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
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    target_role: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=AnalysisStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    deterministic_checks: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    analysis_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )
    prompt_version: Mapped[str] = mapped_column(
        String(32),
        default="v1.0.0",
        nullable=False,
    )
    schema_version: Mapped[str] = mapped_column(
        String(32),
        default="v1.0.0",
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
    candidate = relationship("CandidateProfile", back_populates="analyses")
    resume = relationship("Resume", back_populates="analyses")

    __table_args__ = (
        Index("idx_analyses_candidate_created", "candidate_id", "created_at"),
        Index("idx_analyses_resume_created", "resume_id", "created_at"),
        Index("idx_analyses_resume_status", "resume_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<ResumeAnalysis id={self.id} candidate_id={self.candidate_id} status={self.status} target_role={self.target_role}>"
