import re
import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.models.job import EmploymentType, JobStatus, WorkplaceType


def normalize_skill_list(skills: Optional[List[str]]) -> List[str]:
    """Validate and normalize skills list: strip whitespace, reject empties, deduplicate."""
    if skills is None:
        return []
    cleaned: List[str] = []
    seen = set()
    for s in skills:
        if not isinstance(s, str):
            raise ValueError("Skill entry must be a string")
        trimmed = s.strip()
        if not trimmed:
            raise ValueError("Skill names must not be empty or whitespace only")
        key = trimmed.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(trimmed)
    return cleaned


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    slug: Optional[str] = Field(None, max_length=255, description="Custom or generated slug")
    department: Optional[str] = Field(None, max_length=128, description="Department name")
    description: str = Field(..., min_length=1, description="Detailed job description")
    responsibilities: Optional[str] = Field(None, description="Key responsibilities")
    qualifications: Optional[str] = Field(None, description="Required qualifications")
    location: Optional[str] = Field(None, max_length=255, description="Work location")
    workplace_type: WorkplaceType = Field(
        default=WorkplaceType.ONSITE, description="Workplace type"
    )
    employment_type: EmploymentType = Field(
        default=EmploymentType.FULL_TIME, description="Employment type"
    )
    experience_min: Optional[int] = Field(None, ge=0, description="Minimum experience in years")
    experience_max: Optional[int] = Field(None, ge=0, description="Maximum experience in years")
    salary_min: Optional[float] = Field(None, ge=0, description="Minimum salary")
    salary_max: Optional[float] = Field(None, ge=0, description="Maximum salary")
    salary_currency: str = Field(default="INR", max_length=10, description="Salary currency")
    required_skills: List[str] = Field(default_factory=list, description="Mandatory skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills")

    @field_validator("title", "description", mode="before")
    @classmethod
    def check_non_empty_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or whitespace only")
            return v_stripped
        return v

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def validate_skills_list(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("Skills must be provided as a list")
        return normalize_skill_list(v)

    @model_validator(mode="after")
    def validate_job_bounds_and_skills(self) -> "JobBase":
        # Experience range validation
        if self.experience_min is not None and self.experience_max is not None:
            if self.experience_min > self.experience_max:
                raise ValueError("experience_min cannot be greater than experience_max")

        # Salary range validation
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min cannot be greater than salary_max")

        # Overlap check between required and preferred skills
        req_set = {s.strip().lower() for s in (self.required_skills or []) if s}
        for p in self.preferred_skills or []:
            if p and p.strip().lower() in req_set:
                raise ValueError(
                    f"Skill '{p.strip()}' cannot appear in both required and preferred skills"
                )

        return self


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = Field(None, min_length=1)
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    workplace_type: Optional[WorkplaceType] = None
    employment_type: Optional[EmploymentType] = None
    experience_min: Optional[int] = Field(None, ge=0)
    experience_max: Optional[int] = Field(None, ge=0)
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    salary_currency: Optional[str] = Field(None, max_length=10)
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None

    @field_validator("title", "description", mode="before")
    @classmethod
    def check_non_empty_strings(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str):
            v_stripped = v.strip()
            if not v_stripped:
                raise ValueError("Field cannot be empty or whitespace only")
            return v_stripped
        return v

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def validate_skills_list(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("Skills must be provided as a list")
        return normalize_skill_list(v)

    @model_validator(mode="after")
    def validate_update_bounds_and_skills(self) -> "JobUpdate":
        if self.experience_min is not None and self.experience_max is not None:
            if self.experience_min > self.experience_max:
                raise ValueError("experience_min cannot be greater than experience_max")

        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min cannot be greater than salary_max")

        if self.required_skills is not None and self.preferred_skills is not None:
            req_set = {s.strip().lower() for s in self.required_skills if s}
            for p in self.preferred_skills:
                if p and p.strip().lower() in req_set:
                    raise ValueError(
                        f"Skill '{p.strip()}' cannot appear in both required and preferred skills"
                    )

        return self


class JobResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    title: str
    slug: Optional[str] = None
    department: Optional[str] = None
    description: str
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    location: Optional[str] = None
    workplace_type: str
    employment_type: str
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str
    required_skills: List[str]
    preferred_skills: List[str]
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicJobResponse(BaseModel):
    id: uuid.UUID
    title: str
    slug: Optional[str] = None
    organization_name: str
    department: Optional[str] = None
    description: str
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    location: Optional[str] = None
    workplace_type: str
    employment_type: str
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str
    required_skills: List[str]
    preferred_skills: List[str]
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedJobResponse(BaseModel):
    items: List[JobResponse]
    total: int
    limit: int
    offset: int


class PaginatedPublicJobResponse(BaseModel):
    items: List[PublicJobResponse]
    total: int
    limit: int
    offset: int
