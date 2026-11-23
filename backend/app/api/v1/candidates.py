from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.candidate import (
    CandidateProfileCreate,
    CandidateProfileResponse,
    CandidateProfileUpdate,
)
from app.services.resume_service import (
    create_candidate_profile,
    get_candidate_profile_by_user_id,
    update_candidate_profile,
)

router = APIRouter()


@router.get(
    "/me/profile",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current candidate profile",
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    """Retrieve the candidate profile for the currently authenticated user."""
    profile = await get_candidate_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found. Create one using POST /api/v1/candidates/me/profile",
        )

    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=profile.phone,
        location=profile.location,
        headline=profile.headline,
        professional_summary=profile.professional_summary,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.post(
    "/me/profile",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create candidate profile",
)
async def create_my_profile(
    profile_in: CandidateProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    """Create a new candidate profile for the authenticated user."""
    profile = await create_candidate_profile(db, user=current_user, profile_in=profile_in)
    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=profile.phone,
        location=profile.location,
        headline=profile.headline,
        professional_summary=profile.professional_summary,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.patch(
    "/me/profile",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update candidate profile",
)
async def update_my_profile(
    update_in: CandidateProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileResponse:
    """Update fields on the authenticated user's candidate profile."""
    profile = await get_candidate_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )

    profile = await update_candidate_profile(db, profile=profile, update_in=update_in)
    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=profile.phone,
        location=profile.location,
        headline=profile.headline,
        professional_summary=profile.professional_summary,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
