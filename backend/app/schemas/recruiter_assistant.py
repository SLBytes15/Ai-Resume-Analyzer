import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


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


class RecruiterMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    context_metadata: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecruiterConversationCreateRequest(BaseModel):
    conversation_title: Optional[str] = Field(None, max_length=255, description="Optional title for the conversation")
    conversation_type: RecruiterConversationType = Field(
        default=RecruiterConversationType.GENERAL_HIRING,
        description="Type of hiring intelligence discussion"
    )
    initial_message: Optional[str] = Field(None, max_length=4000, description="Optional initial question")


class RecruiterConversationUpdateRequest(BaseModel):
    conversation_title: Optional[str] = Field(None, max_length=255)
    is_archived: Optional[bool] = None


class RecruiterConversationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by_user_id: uuid.UUID
    conversation_title: str
    conversation_type: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    last_message: Optional[RecruiterMessageResponse] = None

    model_config = ConfigDict(from_attributes=True)


class RecruiterConversationDetailResponse(RecruiterConversationResponse):
    messages: List[RecruiterMessageResponse] = []


class RecruiterMessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000, description="Recruiter question or query")
    job_id: Optional[uuid.UUID] = Field(None, description="Optional specific job focus")
    application_id: Optional[uuid.UUID] = Field(None, description="Optional specific candidate application focus")


class RecruiterMessageResponsePayload(BaseModel):
    user_message: RecruiterMessageResponse
    assistant_message: RecruiterMessageResponse
