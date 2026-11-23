import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class ScreeningRunStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ScreeningResultStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScreeningInsightStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScreeningConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ScreeningRun(Base):
    __tablename__ = "screening_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=ScreeningRunStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    total_applications: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    processed_applications: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    failed_applications: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    scoring_config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    job_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    error_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    organization = relationship("Organization")
    job = relationship("Job")
    actor = relationship("User")
    results = relationship(
        "ScreeningResult",
        back_populates="screening_run",
        cascade="all, delete-orphan",
        order_by="desc(ScreeningResult.total_score)",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'PARTIAL', 'FAILED')",
            name="ck_screening_runs_status_valid",
        ),
        Index("idx_screening_runs_org_job", "organization_id", "job_id"),
        Index("idx_screening_runs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ScreeningRun id={self.id} job_id={self.job_id} status={self.status}>"


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    screening_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screening_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    submitted_resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    resume_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    total_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        index=True,
    )
    required_skill_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    preferred_skill_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    experience_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    matched_skills: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    missing_evidence: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    preferred_skill_matches: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    experience_assessment: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    evidence_items: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    confidence_level: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )
    processing_status: Mapped[str] = mapped_column(
        String(32),
        default=ScreeningResultStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    screening_run = relationship("ScreeningRun", back_populates="results")
    application = relationship("Application")
    organization = relationship("Organization")
    job = relationship("Job")
    candidate = relationship("CandidateProfile")
    submitted_resume = relationship("Resume")
    insight = relationship(
        "ScreeningInsight",
        back_populates="screening_result",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "screening_run_id",
            "application_id",
            name="uq_screening_run_application",
        ),
        CheckConstraint(
            "processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')",
            name="ck_screening_results_status_valid",
        ),
        CheckConstraint(
            "total_score IS NULL OR (total_score >= 0 AND total_score <= 100)",
            name="ck_screening_results_total_score",
        ),
        Index("idx_screening_results_org_job", "organization_id", "job_id"),
        Index("idx_screening_results_run_score", "screening_run_id", "total_score"),
        Index("idx_screening_results_candidate", "candidate_id"),
    )

    def __repr__(self) -> str:
        return f"<ScreeningResult id={self.id} run={self.screening_run_id} score={self.total_score}>"


class ScreeningInsight(Base):
    __tablename__ = "screening_insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    screening_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screening_results.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    screening_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screening_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=ScreeningInsightStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    model_id: Mapped[str] = mapped_column(
        String(64),
        default="qwen3:4b",
        nullable=False,
    )
    prompt_version: Mapped[str] = mapped_column(
        String(32),
        default="v1.0.0",
        nullable=False,
    )
    insight_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    screening_result = relationship("ScreeningResult", back_populates="insight")
    screening_run = relationship("ScreeningRun")
    application = relationship("Application")

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'FAILED')",
            name="ck_screening_insights_status_valid",
        ),
        Index("idx_screening_insights_run_result", "screening_run_id", "screening_result_id"),
    )

    def __repr__(self) -> str:
        return f"<ScreeningInsight id={self.id} result_id={self.screening_result_id} status={self.status}>"
