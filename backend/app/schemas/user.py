import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters long",
    )


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
