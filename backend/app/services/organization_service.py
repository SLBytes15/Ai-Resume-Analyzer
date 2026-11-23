import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.user import User
from app.schemas.organization import OrganizationCreate, slugify
from app.services.auth_service import get_user_by_email


async def get_organization_by_id(
    db: AsyncSession, org_id: uuid.UUID
) -> Optional[Organization]:
    """Fetch organization by primary key UUID."""
    stmt = select(Organization).where(Organization.id == org_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_organization_by_slug(
    db: AsyncSession, slug: str
) -> Optional[Organization]:
    """Fetch organization by unique slug."""
    stmt = select(Organization).where(Organization.slug == slug.strip().lower())
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_organization(
    db: AsyncSession, creator: User, org_in: OrganizationCreate
) -> Tuple[Organization, OrganizationMembership]:
    """Create an organization and establish creator as OWNER in a single transaction."""
    # Determine unique slug
    if org_in.slug:
        slug = org_in.slug.strip().lower()
        existing = await get_organization_by_slug(db, slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization slug '{slug}' is already taken",
            )
    else:
        base_slug = slugify(org_in.name) or "org"
        slug = base_slug
        counter = 1
        while await get_organization_by_slug(db, slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

    org = Organization(
        name=org_in.name.strip(),
        slug=slug,
        is_active=True,
    )
    db.add(org)
    await db.flush()  # Generate org.id

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=creator.id,
        role=OrganizationRole.OWNER,
        is_active=True,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(org)
    await db.refresh(membership)

    return org, membership


async def get_user_organizations(
    db: AsyncSession, user_id: uuid.UUID
) -> List[Tuple[Organization, OrganizationRole]]:
    """List all organizations where user has active membership."""
    stmt = (
        select(Organization, OrganizationMembership.role)
        .join(
            OrganizationMembership,
            Organization.id == OrganizationMembership.organization_id,
        )
        .where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active == True,
            Organization.is_active == True,
        )
        .order_by(Organization.name)
    )
    result = await db.execute(stmt)
    return result.all()


async def get_organization_membership(
    db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[OrganizationMembership]:
    """Fetch active membership for a specific user and organization."""
    stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.is_active == True,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_organization_members(
    db: AsyncSession, org_id: uuid.UUID
) -> List[Tuple[OrganizationMembership, User]]:
    """List all active members of an organization with their user profiles."""
    stmt = (
        select(OrganizationMembership, User)
        .join(User, OrganizationMembership.user_id == User.id)
        .where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.is_active == True,
        )
        .order_by(OrganizationMembership.created_at)
    )
    result = await db.execute(stmt)
    return result.all()


async def add_member(
    db: AsyncSession,
    org_id: uuid.UUID,
    caller_role: OrganizationRole,
    target_email: str,
    role: OrganizationRole,
) -> Tuple[OrganizationMembership, User]:
    """Add a user to the organization by email."""
    # Caller authorization: only OWNER or ADMIN can add members
    if caller_role not in (OrganizationRole.OWNER, OrganizationRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization OWNER or ADMIN can add members",
        )

    # Invariant: cannot add another OWNER directly
    if role == OrganizationRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organization can have only one OWNER. Use transfer ownership.",
        )

    # ADMIN cannot add another ADMIN unless permitted
    if caller_role == OrganizationRole.ADMIN and role == OrganizationRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER can assign ADMIN role",
        )

    # Lookup target user
    target_user = await get_user_by_email(db, target_email)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{target_email}' does not exist on the platform",
        )

    # Check if membership already exists
    existing = await get_organization_membership(db, org_id, target_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    membership = OrganizationMembership(
        organization_id=org_id,
        user_id=target_user.id,
        role=role,
        is_active=True,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)

    return membership, target_user


async def update_member_role(
    db: AsyncSession,
    org_id: uuid.UUID,
    caller_membership: OrganizationMembership,
    target_user_id: uuid.UUID,
    new_role: OrganizationRole,
) -> Tuple[OrganizationMembership, User]:
    """Update a member's role or transfer ownership."""
    # Caller authorization
    if caller_membership.role not in (OrganizationRole.OWNER, OrganizationRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization OWNER or ADMIN can modify member roles",
        )

    # Fetch target membership
    stmt = (
        select(OrganizationMembership, User)
        .join(User, OrganizationMembership.user_id == User.id)
        .where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == target_user_id,
            OrganizationMembership.is_active == True,
        )
    )
    result = await db.execute(stmt)
    target = result.first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization",
        )
    target_membership, target_user = target

    # Invariant: Prevent removal or direct demotion of the OWNER
    if target_membership.role == OrganizationRole.OWNER and new_role != OrganizationRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote the active organization OWNER. Transfer ownership to another member instead.",
        )

    # Ownership transfer: single active OWNER invariant
    if new_role == OrganizationRole.OWNER:
        if caller_membership.role != OrganizationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the current OWNER can transfer organization ownership",
            )
        # Atomically demote current owner to ADMIN and promote target to OWNER
        # Flush the demotion first so the unique partial index uq_org_active_owner is freed
        caller_membership.role = OrganizationRole.ADMIN
        await db.flush()
        target_membership.role = OrganizationRole.OWNER
        await db.commit()
        await db.refresh(target_membership)
        return target_membership, target_user

    # ADMIN permissions: cannot modify OWNER or another ADMIN
    if caller_membership.role == OrganizationRole.ADMIN:
        if target_membership.role in (OrganizationRole.OWNER, OrganizationRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ADMIN cannot modify role of OWNER or another ADMIN",
            )
        if new_role == OrganizationRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only OWNER can promote a member to ADMIN",
            )

    target_membership.role = new_role
    await db.commit()
    await db.refresh(target_membership)
    return target_membership, target_user


async def remove_member(
    db: AsyncSession,
    org_id: uuid.UUID,
    caller_membership: OrganizationMembership,
    target_user_id: uuid.UUID,
) -> None:
    """Remove a member from the organization."""
    # Self-leave is allowed for non-owners
    is_self = caller_membership.user_id == target_user_id

    if not is_self and caller_membership.role not in (
        OrganizationRole.OWNER,
        OrganizationRole.ADMIN,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER or ADMIN can remove members",
        )

    # Fetch target membership
    target_membership = await get_organization_membership(db, org_id, target_user_id)
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization",
        )

    # Invariant: Prevent removal of the OWNER
    if target_membership.role == OrganizationRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the organization OWNER. Transfer ownership first.",
        )

    # ADMIN cannot remove another ADMIN
    if not is_self and caller_membership.role == OrganizationRole.ADMIN:
        if target_membership.role in (OrganizationRole.OWNER, OrganizationRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ADMIN cannot remove another ADMIN or OWNER",
            )

    await db.delete(target_membership)
    await db.commit()
