import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import Depends, Header, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.user import User
from app.services.auth_service import get_user_by_id
from app.services.organization_service import (
    get_organization_by_id,
    get_organization_membership,
)

http_bearer = HTTPBearer(auto_error=True)


async def get_current_user_and_token(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> Tuple[User, Dict[str, Any]]:
    """Validate JWT token and return authenticated user along with decoded token claims."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception

    return user, payload


async def get_current_user(
    user_token: Tuple[User, Dict[str, Any]] = Depends(get_current_user_and_token),
) -> User:
    """Return authenticated User."""
    user, _ = user_token
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure authenticated user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
        )
    return current_user


async def get_org_membership_from_path(
    org_id: uuid.UUID = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Tuple[Organization, OrganizationMembership]:
    """Dependency verifying caller has active membership in the organization given by path {org_id}."""
    org = await get_organization_by_id(db, org_id)
    if not org or not org.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    membership = await get_organization_membership(db, org_id, current_user.id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    return org, membership


async def get_org_membership_from_org_id_path(
    organization_id: uuid.UUID = Path(..., description="Organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Tuple[Organization, OrganizationMembership]:
    """Dependency verifying caller has active membership in the organization given by path {organization_id}."""
    org = await get_organization_by_id(db, organization_id)
    if not org or not org.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    membership = await get_organization_membership(db, organization_id, current_user.id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    return org, membership


def require_job_role(allowed_roles: List[OrganizationRole]):
    """Factory dependency checking caller role for job operations."""
    async def role_checker(
        org_and_membership: Tuple[Organization, OrganizationMembership] = Depends(
            get_org_membership_from_org_id_path
        ),
    ) -> Tuple[Organization, OrganizationMembership]:
        _, membership = org_and_membership
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return org_and_membership

    return role_checker


def require_role(allowed_roles: List[OrganizationRole]):
    """Factory dependency checking caller role in the organization."""
    async def role_checker(
        org_and_membership: Tuple[Organization, OrganizationMembership] = Depends(
            get_org_membership_from_path
        ),
    ) -> Tuple[Organization, OrganizationMembership]:
        _, membership = org_and_membership
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return org_and_membership

    return role_checker


async def get_active_recruiter_context(
    user_token: Tuple[User, Dict[str, Any]] = Depends(get_current_user_and_token),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    db: AsyncSession = Depends(get_db),
) -> Tuple[User, Organization, OrganizationMembership]:
    """
    Validate active recruiter organization context.
    Extracts active_org_id from token claims or X-Organization-Id header,
    and verifies active membership in that organization.
    """
    user, payload = user_token
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
        )

    # Org ID from JWT claim or header
    org_id_val = payload.get("active_org_id") or x_organization_id
    if not org_id_val:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active organization context selected. Switch organization context first.",
        )

    try:
        org_id = uuid.UUID(str(org_id_val))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid organization context ID format",
        )

    org = await get_organization_by_id(db, org_id)
    if not org or not org.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active organization context is invalid or inactive",
        )

    membership = await get_organization_membership(db, org_id, user.id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have active membership in this organization context",
        )

    return user, org, membership
