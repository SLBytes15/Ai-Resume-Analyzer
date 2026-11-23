import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_active_user,
    get_org_membership_from_path,
    require_role,
)
from app.core.database import get_db
from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.user import User
from app.schemas.organization import (
    MemberAddRequest,
    MemberResponse,
    MemberUpdateRequest,
    OrganizationCreate,
    OrganizationResponse,
)
from app.services.organization_service import (
    add_member,
    create_organization,
    get_organization_members,
    get_user_organizations,
    remove_member,
    update_member_role,
)

router = APIRouter()


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_new_organization(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """Create a new organization. The creator is atomically assigned as the organization OWNER."""
    org, membership = await create_organization(db, creator=current_user, org_in=org_in)
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        created_at=org.created_at,
        updated_at=org.updated_at,
        role=membership.role,
    )


@router.get(
    "",
    response_model=List[OrganizationResponse],
    status_code=status.HTTP_200_OK,
    summary="List organizations current user belongs to",
)
async def list_user_organizations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[OrganizationResponse]:
    """Retrieve all organizations where current user holds an active membership."""
    orgs_with_role = await get_user_organizations(db, current_user.id)
    return [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at,
            role=role,
        )
        for org, role in orgs_with_role
    ]


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get organization details",
)
async def get_organization_details(
    org_and_membership=Depends(get_org_membership_from_path),
) -> OrganizationResponse:
    """Get organization details for members."""
    org, membership = org_and_membership
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        is_active=org.is_active,
        created_at=org.created_at,
        updated_at=org.updated_at,
        role=membership.role,
    )


@router.get(
    "/{org_id}/members",
    response_model=List[MemberResponse],
    status_code=status.HTTP_200_OK,
    summary="List organization members",
)
async def list_members(
    org_and_membership=Depends(get_org_membership_from_path),
    db: AsyncSession = Depends(get_db),
) -> List[MemberResponse]:
    """List all active members belonging to this organization."""
    org, _ = org_and_membership
    members_with_users = await get_organization_members(db, org.id)
    return [
        MemberResponse(
            id=membership.id,
            organization_id=membership.organization_id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=membership.role,
            is_active=membership.is_active,
            created_at=membership.created_at,
            updated_at=membership.updated_at,
        )
        for membership, user in members_with_users
    ]


@router.post(
    "/{org_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new member to the organization",
)
async def add_new_member(
    member_in: MemberAddRequest,
    org_and_membership=Depends(
        require_role([OrganizationRole.OWNER, OrganizationRole.ADMIN])
    ),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Add an existing platform user to this organization by email. Requires OWNER or ADMIN role."""
    org, caller_membership = org_and_membership
    membership, target_user = await add_member(
        db,
        org_id=org.id,
        caller_role=caller_membership.role,
        target_email=member_in.email,
        role=member_in.role,
    )
    return MemberResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        is_active=membership.is_active,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )


@router.put(
    "/{org_id}/members/{user_id}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a member's role or transfer ownership",
)
async def update_member(
    update_in: MemberUpdateRequest,
    user_id: uuid.UUID = Path(..., description="Target member's user ID"),
    org_and_membership=Depends(
        require_role([OrganizationRole.OWNER, OrganizationRole.ADMIN])
    ),
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Update a member's role. If promoted to OWNER, ownership transfers atomically from caller."""
    org, caller_membership = org_and_membership
    membership, target_user = await update_member_role(
        db,
        org_id=org.id,
        caller_membership=caller_membership,
        target_user_id=user_id,
        new_role=update_in.role,
    )
    return MemberResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        is_active=membership.is_active,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove a member from the organization",
)
async def delete_member(
    user_id: uuid.UUID = Path(..., description="Target member's user ID"),
    org_and_membership=Depends(get_org_membership_from_path),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a member from the organization. Cannot remove the organization OWNER."""
    org, caller_membership = org_and_membership
    await remove_member(
        db,
        org_id=org.id,
        caller_membership=caller_membership,
        target_user_id=user_id,
    )
    return {"message": "Member removed successfully"}
