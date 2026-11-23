import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.application import ApplicationStatus


class ApplicationSubmitRequest(BaseModel):
    resume_id: uuid.UUID = Field(..., description="UUID of the candidate's resume to pin")
    cover_letter: Optional[str] = Field(None, max_length=10000, description="Optional cover letter")


class ApplicationStatusUpdateRequest(BaseModel):
    status: ApplicationStatus = Field(..., description="Target application status")
    internal_note: Optional[str] = Field(None, max_length=5000, description="Optional recruiter internal note")


class StatusHistoryItemResponse(BaseModel):
    id: uuid.UUID
    previous_status: Optional[str] = None
    new_status: str
    changed_by: Optional[uuid.UUID] = None
    changed_at: datetime
    internal_note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CandidateApplicationResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    job_title: str
    organization_id: uuid.UUID
    organization_name: str
    submitted_resume_id: uuid.UUID
    resume_filename: str
    status: str
    cover_letter: Optional[str] = None
    submitted_at: datetime
    status_updated_at: datetime
    withdrawn_at: Optional[datetime] = None
    job_location: Optional[str] = None
    workplace_type: Optional[str] = None
    employment_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecruiterApplicationListItem(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    job_title: str
    organization_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_headline: Optional[str] = None
    submitted_resume_id: uuid.UUID
    resume_filename: str
    status: str
    submitted_at: datetime
    status_updated_at: datetime
    withdrawn_at: Optional[datetime] = None
    cover_letter: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecruiterApplicationDetailResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    job_title: str
    organization_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_headline: Optional[str] = None
    submitted_resume_id: uuid.UUID
    resume_filename: str
    status: str
    submitted_at: datetime
    status_updated_at: datetime
    withdrawn_at: Optional[datetime] = None
    cover_letter: Optional[str] = None
    candidate_snapshot: Optional[Dict[str, Any]] = None
    status_history: List[StatusHistoryItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedCandidateApplicationsResponse(BaseModel):
    items: List[CandidateApplicationResponse]
    total: int
    limit: int
    offset: int


class PaginatedRecruiterApplicationsResponse(BaseModel):
    items: List[RecruiterApplicationListItem]
    total: int
    limit: int
    offset: int
