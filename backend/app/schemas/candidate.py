import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CandidateProfileBase(BaseModel):
    phone: Optional[str] = Field(None, max_length=32)
    location: Optional[str] = Field(None, max_length=128)
    headline: Optional[str] = Field(None, max_length=255)
    professional_summary: Optional[str] = None


class CandidateProfileCreate(CandidateProfileBase):
    pass


class CandidateProfileUpdate(BaseModel):
    phone: Optional[str] = Field(None, max_length=32)
    location: Optional[str] = Field(None, max_length=128)
    headline: Optional[str] = Field(None, max_length=255)
    professional_summary: Optional[str] = None


class CandidateProfileResponse(CandidateProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
