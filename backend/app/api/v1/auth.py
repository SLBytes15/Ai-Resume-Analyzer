from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.organization import (
    SwitchOrganizationRequest,
    SwitchOrganizationResponse,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_user,
    get_user_by_email,
)
from app.services.organization_service import (
    get_organization_by_id,
    get_organization_membership,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new global user account, hash the password, and return JWT token."""
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await create_user(db, user_in)
    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in user and obtain JWT token",
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate user with email and password, returning JWT token."""
    user = await authenticate_user(
        db, email=login_data.email, password=login_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return the profile of currently authenticated user. Never exposes password hash."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/switch-organization",
    response_model=SwitchOrganizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Switch active organization context and issue scoped JWT",
)
async def switch_organization(
    switch_in: SwitchOrganizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SwitchOrganizationResponse:
    """
    Select an active organization context.
    Verifies user has active membership in the target organization,
    and returns a newly signed JWT carrying active_org_id and org_role claims.
    """
    org = await get_organization_by_id(db, switch_in.organization_id)
    if not org or not org.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    membership = await get_organization_membership(db, org.id, current_user.id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an active member of this organization",
        )

    extra_claims = {
        "active_org_id": str(org.id),
        "org_role": membership.role.value if hasattr(membership.role, "value") else str(membership.role),
    }
    new_token = create_access_token(subject=str(current_user.id), extra_claims=extra_claims)

    return SwitchOrganizationResponse(
        message="Switched active organization context.",
        access_token=new_token,
        token_type="bearer",
        active_org_id=org.id,
        org_name=org.name,
        org_role=membership.role,
    )
