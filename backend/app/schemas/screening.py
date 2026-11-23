import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StrengthCategory(str, Enum):
    SKILL = "SKILL"
    EXPERIENCE = "EXPERIENCE"
    PROJECT = "PROJECT"
    EDUCATION = "EDUCATION"
    CERTIFICATION = "CERTIFICATION"


class KeyStrength(BaseModel):
    title: str = Field(..., description="Short descriptive title of the strength")
    description: str = Field(..., description="Evidence-backed description grounded in resume")
    supporting_evidence: List[str] = Field(default_factory=list, description="Verbatim or traceable excerpts from resume")
    category: StrengthCategory = Field(StrengthCategory.SKILL)


class RelevantProject(BaseModel):
    project_name: str = Field(..., description="Name of the relevant project")
    description: str = Field(..., description="Factual description grounded in resume evidence")
    relevant_requirements: List[str] = Field(default_factory=list, description="Job skills/requirements demonstrated")
    supporting_evidence: List[str] = Field(default_factory=list, description="Verbatim snippets from project evidence")


class EvidenceGap(BaseModel):
    requirement: str = Field(..., description="Job requirement name")
    explanation: str = Field(..., description="Neutral explanation (e.g. No supporting evidence was identified in the submitted resume)")


class CandidateInsightSchema(BaseModel):
    summary: str = Field(..., description="1-2 sentence concise explanation of resume alignment with job requirements")
    key_strengths: List[KeyStrength] = Field(default_factory=list)
    relevant_projects: List[RelevantProject] = Field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list, description="Ambiguities such as missing employment dates")
    score_explanation: str = Field(..., description="Explanation of how demonstrated evidence supports the deterministic score")


class ScreeningInsightResponse(BaseModel):
    id: uuid.UUID
    screening_result_id: uuid.UUID
    screening_run_id: uuid.UUID
    application_id: uuid.UUID
    status: str
    model_id: str
    prompt_version: str
    insight_data: CandidateInsightSchema
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreeningTriggerRequest(BaseModel):
    scoring_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Optional custom weights: {'required_skills': 0.6, 'preferred_skills': 0.15, 'experience': 0.25}",
    )


class ScreeningRunResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    triggered_by: Optional[uuid.UUID] = None
    status: str
    total_applications: int
    processed_applications: int
    failed_applications: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    scoring_config: Dict[str, Any] = {}
    job_snapshot: Dict[str, Any] = {}
    error_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ScreeningResultListItem(BaseModel):
    id: uuid.UUID
    screening_run_id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_headline: Optional[str] = None
    submitted_resume_id: uuid.UUID
    resume_filename: Optional[str] = None
    total_score: Optional[float] = None
    required_skill_score: Optional[float] = None
    preferred_skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    matched_skills_count: int = 0
    missing_evidence_count: int = 0
    confidence_level: Optional[str] = None
    processing_status: str
    insight_summary: Optional[str] = None
    insight_status: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreeningResultDetailResponse(BaseModel):
    id: uuid.UUID
    screening_run_id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_headline: Optional[str] = None
    submitted_resume_id: uuid.UUID
    resume_filename: Optional[str] = None
    total_score: Optional[float] = None
    required_skill_score: Optional[float] = None
    preferred_skill_score: Optional[float] = None
    experience_score: Optional[float] = None
    matched_skills: List[Dict[str, Any]] = []
    missing_evidence: List[Dict[str, Any]] = []
    preferred_skill_matches: List[Dict[str, Any]] = []
    experience_assessment: Dict[str, Any] = {}
    explanation: str
    confidence_level: Optional[str] = None
    processing_status: str
    error_message: Optional[str] = None
    insight: Optional[ScreeningInsightResponse] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedScreeningResultsResponse(BaseModel):
    items: List[ScreeningResultListItem]
    total: int
    limit: int
    offset: int


class PaginatedScreeningRunsResponse(BaseModel):
    items: List[ScreeningRunResponse]
    total: int
    limit: int
    offset: int
