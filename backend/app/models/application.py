import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class ApplicationStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEWING = "INTERVIEWING"
    REJECTED = "REJECTED"
    HIRED = "HIRED"
    WITHDRAWN = "WITHDRAWN"


# Permitted recruiter transitions
ALLOWED_RECRUITER_TRANSITIONS = {
    ApplicationStatus.SUBMITTED.value: [
        ApplicationStatus.UNDER_REVIEW.value,
        ApplicationStatus.SHORTLISTED.value,
        ApplicationStatus.REJECTED.value,
    ],
    ApplicationStatus.UNDER_REVIEW.value: [
        ApplicationStatus.SHORTLISTED.value,
        ApplicationStatus.REJECTED.value,
    ],
    ApplicationStatus.SHORTLISTED.value: [
        ApplicationStatus.INTERVIEWING.value,
        ApplicationStatus.HIRED.value,
        ApplicationStatus.REJECTED.value,
    ],
    ApplicationStatus.INTERVIEWING.value: [
        ApplicationStatus.HIRED.value,
        ApplicationStatus.REJECTED.value,
    ],
}

# Permitted candidate transitions
ALLOWED_CANDIDATE_TRANSITIONS = {
    ApplicationStatus.SUBMITTED.value: [ApplicationStatus.WITHDRAWN.value],
    ApplicationStatus.UNDER_REVIEW.value: [ApplicationStatus.WITHDRAWN.value],
    ApplicationStatus.SHORTLISTED.value: [ApplicationStatus.WITHDRAWN.value],
    ApplicationStatus.INTERVIEWING.value: [ApplicationStatus.WITHDRAWN.value],
}


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=ApplicationStatus.SUBMITTED.value,
        nullable=False,
        index=True,
    )
    cover_letter: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    candidate_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
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
    status_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    job = relationship("Job", back_populates="applications")
    candidate = relationship("CandidateProfile", back_populates="applications")
    submitted_resume = relationship("Resume", foreign_keys=[submitted_resume_id])
    organization = relationship("Organization", back_populates="applications")
    status_history = relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="asc(ApplicationStatusHistory.changed_at)",
    )

    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate_application"),
        CheckConstraint(
            "status IN ('SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'INTERVIEWING', 'REJECTED', 'HIRED', 'WITHDRAWN')",
            name="ck_applications_status_valid",
        ),
        Index("idx_applications_org_status", "organization_id", "status"),
        Index("idx_applications_job_status", "job_id", "status"),
        Index("idx_applications_candidate_status", "candidate_id", "status"),
        Index("idx_applications_submitted_at", "submitted_at"),
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} job={self.job_id} candidate={self.candidate_id} status={self.status}>"


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_status: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
    )
    new_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    internal_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    application = relationship("Application", back_populates="status_history")
    actor = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "new_status IN ('SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'INTERVIEWING', 'REJECTED', 'HIRED', 'WITHDRAWN')",
            name="ck_status_history_new_status_valid",
        ),
        Index("idx_app_status_hist_app_id", "application_id"),
        Index("idx_app_status_hist_changed_at", "changed_at"),
    )

    def __repr__(self) -> str:
        return f"<ApplicationStatusHistory id={self.id} app={self.application_id} {self.previous_status}->{self.new_status}>"
