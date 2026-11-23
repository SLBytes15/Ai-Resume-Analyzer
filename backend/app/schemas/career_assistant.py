import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


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


class CareerMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    context_metadata: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareerConversationCreateRequest(BaseModel):
    resume_id: Optional[uuid.UUID] = Field(None, description="Optional resume version to ground the conversation")
    target_role: Optional[str] = Field(None, max_length=128, description="Target career role (e.g. Backend Developer)")
    conversation_purpose: ConversationPurpose = Field(
        default=ConversationPurpose.GENERAL,
        description="Primary focus: CAREER_GUIDANCE, SKILL_DEVELOPMENT, INTERVIEW_PREP, etc."
    )
    title: Optional[str] = Field(None, max_length=255, description="Custom conversation title")
    initial_message: Optional[str] = Field(None, max_length=2000, description="Optional opening question")


class CareerConversationUpdateRequest(BaseModel):
    conversation_title: Optional[str] = Field(None, max_length=255)
    is_archived: Optional[bool] = None


class CareerConversationResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    resume_id: Optional[uuid.UUID] = None
    resume_sha256: Optional[str] = None
    target_role: Optional[str] = None
    conversation_title: str
    conversation_type: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    last_message: Optional[CareerMessageResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CareerConversationDetailResponse(CareerConversationResponse):
    messages: List[CareerMessageResponse] = []


class CareerMessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=3000, description="Candidate message content")
    include_m7_analysis: bool = Field(True, description="Whether to include M7 qualitative analysis findings in context")


class CareerMessageResponsePayload(BaseModel):
    user_message: CareerMessageResponse
    assistant_message: CareerMessageResponse
