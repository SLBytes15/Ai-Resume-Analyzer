import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ImprovementPriorityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class StrengthItem(BaseModel):
    title: str = Field(..., description="Short title describing the strength")
    description: str = Field(..., description="Explanation of how the strength is demonstrated")
    supporting_evidence: List[str] = Field(default_factory=list, description="Direct snippets or references from resume")


class SkillsAnalysis(BaseModel):
    demonstrated_skills: List[str] = Field(
        default_factory=list,
        description="Skills supported by project or employment context in the resume"
    )
    skills_with_limited_evidence: List[str] = Field(
        default_factory=list,
        description="Skills listed as keywords but lacking elaboration or supporting evidence"
    )


class ProjectAnalysisItem(BaseModel):
    project_name: str = Field(..., description="Project name as extracted from the resume")
    what_is_demonstrated: str = Field(..., description="Technical stack and implementation demonstrated")
    what_is_missing: str = Field(..., description="Missing details such as technical architecture, problem statement, or measurable impact")
    suggested_improvement: str = Field(..., description="Specific suggestion to strengthen this project description")


class ExperienceAnalysisItem(BaseModel):
    role_or_experience: str = Field(..., description="Job title and company or role designation")
    demonstrated_contributions: str = Field(..., description="Core responsibilities and technical tasks evidenced")
    improvement_suggestions: str = Field(..., description="How to better communicate impact, tools, or ownership")


class ImprovementPriorityItem(BaseModel):
    priority: ImprovementPriorityLevel = Field(..., description="Priority level: HIGH, MEDIUM, LOW")
    issue: str = Field(..., description="Identified gap or weakness in resume content")
    why_it_matters: str = Field(..., description="Why recruiters and hiring managers value this information")
    suggested_action: str = Field(..., description="Actionable step candidate should take to resolve this issue")


class TargetRoleAlignment(BaseModel):
    target_role: Optional[str] = Field(None, description="The evaluated target role")
    alignment_summary: str = Field(..., description="Objective assessment of how the resume addresses target role requirements")
    relevant_strengths: List[str] = Field(default_factory=list, description="Demonstrated strengths specifically relevant to this role")
    missing_relevant_evidence: List[str] = Field(default_factory=list, description="Commonly required skills or evidence for this role not found in the resume")


class LLMAnalysisPayload(BaseModel):
    overall_summary: str = Field(..., description="Concise advisory overview of what the resume communicates effectively")
    strengths: List[StrengthItem] = Field(default_factory=list)
    skills_analysis: SkillsAnalysis = Field(default_factory=SkillsAnalysis)
    project_analysis: List[ProjectAnalysisItem] = Field(default_factory=list)
    experience_analysis: List[ExperienceAnalysisItem] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    improvement_priorities: List[ImprovementPriorityItem] = Field(default_factory=list)
    target_role_alignment: Optional[TargetRoleAlignment] = None
    limitations_and_uncertainties: List[str] = Field(default_factory=list)


class DeterministicFinding(BaseModel):
    category: str = Field(..., description="Category of check (e.g. SECTIONS, CONTACT, METRICS, DATES)")
    level: str = Field("INFO", description="Level: INFO, WARNING, ADVISORY")
    message: str = Field(..., description="Explanation of finding and practical guidance")


class DeterministicChecksData(BaseModel):
    word_count: int
    char_count: int
    sections_detected: List[str] = Field(default_factory=list)
    missing_sections: List[str] = Field(default_factory=list)
    empty_or_short_sections: List[str] = Field(default_factory=list)
    contact_info: Dict[str, Any] = Field(default_factory=dict)
    dates_assessment: Dict[str, Any] = Field(default_factory=dict)
    duplicated_content: Dict[str, Any] = Field(default_factory=dict)
    projects_assessment: Dict[str, Any] = Field(default_factory=dict)
    measurable_outcomes: Dict[str, Any] = Field(default_factory=dict)
    findings: List[DeterministicFinding] = Field(default_factory=list)
    layout_notice: str = (
        "Deterministic checks inspect extracted text and data only. Visual styling, margins, fonts, "
        "and physical page layouts cannot be evaluated from plain text."
    )


class ResumeAnalysisCreateRequest(BaseModel):
    target_role: Optional[str] = Field(
        None,
        max_length=128,
        description="Optional target role to tailor career guidance (e.g. Backend Developer, Data Scientist)"
    )


class ResumeAnalysisResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    resume_id: uuid.UUID
    resume_sha256: str
    target_role: Optional[str] = None
    status: str
    deterministic_checks: Optional[DeterministicChecksData] = None
    analysis_data: Optional[LLMAnalysisPayload] = None
    error_message: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: str
    schema_version: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeAnalysisListItem(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    target_role: Optional[str] = None
    status: str
    overall_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
