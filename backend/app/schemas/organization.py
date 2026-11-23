import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models.organization import OrganizationRole


def slugify(name: str) -> str:
    """Generate a clean URL-friendly slug from an organization name."""
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: Optional[str] = Field(
        None,
        min_length=2,
        max_length=64,
        description="Optional unique slug. If omitted, will be auto-generated from name.",
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().lower()
            if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
                raise ValueError(
                    "Slug must contain only lowercase letters, numbers, and hyphens (no trailing or consecutive hyphens)."
                )
        return v


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    role: Optional[OrganizationRole] = Field(
        None, description="Current user's role in this organization"
    )

    model_config = ConfigDict(from_attributes=True)


class MemberAddRequest(BaseModel):
    email: EmailStr
    role: OrganizationRole = Field(
        default=OrganizationRole.RECRUITER,
        description="Role to assign to the new member (ADMIN, RECRUITER, VIEWER).",
    )


class MemberUpdateRequest(BaseModel):
    role: OrganizationRole = Field(
        ...,
        description="Updated role for the member.",
    )


class MemberResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: OrganizationRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SwitchOrganizationRequest(BaseModel):
    organization_id: uuid.UUID


class SwitchOrganizationResponse(BaseModel):
    message: str = "Switched active organization context."
    access_token: str
    token_type: str = "bearer"
    active_org_id: uuid.UUID
    org_name: str
    org_role: OrganizationRole
