import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, utc_now


class JobStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class WorkplaceType(str, Enum):
    ONSITE = "ONSITE"
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"


class EmploymentType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"


class Job(Base):
    __tablename__ = "jobs"

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
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    slug: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    responsibilities: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    qualifications: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    workplace_type: Mapped[str] = mapped_column(
        String(32),
        default=WorkplaceType.ONSITE.value,
        nullable=False,
        index=True,
    )
    employment_type: Mapped[str] = mapped_column(
        String(32),
        default=EmploymentType.FULL_TIME.value,
        nullable=False,
        index=True,
    )
    experience_min: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    experience_max: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    salary_min: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    salary_max: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )
    salary_currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )
    required_skills: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    preferred_skills: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=JobStatus.DRAFT.value,
        nullable=False,
        index=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    organization = relationship("Organization", back_populates="jobs")
    creator = relationship("User")
    applications = relationship(
        "Application",
        back_populates="job",
    )

    __table_args__ = (
        CheckConstraint(
            "experience_min IS NULL OR experience_max IS NULL OR experience_min <= experience_max",
            name="ck_jobs_experience_range",
        ),
        CheckConstraint(
            "(experience_min IS NULL OR experience_min >= 0) AND (experience_max IS NULL OR experience_max >= 0)",
            name="ck_jobs_experience_non_negative",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_jobs_salary_range",
        ),
        CheckConstraint(
            "(salary_min IS NULL OR salary_min >= 0) AND (salary_max IS NULL OR salary_max >= 0)",
            name="ck_jobs_salary_non_negative",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'CLOSED', 'ARCHIVED')",
            name="ck_jobs_status_valid",
        ),
        CheckConstraint(
            "workplace_type IN ('ONSITE', 'REMOTE', 'HYBRID')",
            name="ck_jobs_workplace_type_valid",
        ),
        CheckConstraint(
            "employment_type IN ('FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERNSHIP')",
            name="ck_jobs_employment_type_valid",
        ),
        Index("idx_jobs_org_status", "organization_id", "status"),
        Index("idx_jobs_status_published_at", "status", "published_at"),
        Index("idx_jobs_required_skills", "required_skills", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} org={self.organization_id} title='{self.title}' status={self.status}>"
