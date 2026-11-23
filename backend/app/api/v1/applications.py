import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.application import (
    ApplicationSubmitRequest,
    CandidateApplicationResponse,
    PaginatedCandidateApplicationsResponse,
)
from app.services.application_service import (
    get_candidate_application,
    list_candidate_applications,
    submit_application,
    withdraw_candidate_application,
)

router = APIRouter()


@router.post(
    "/jobs/{job_id}/applications",
    response_model=CandidateApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an application to a published job",
)
async def submit_job_application(
    job_id: uuid.UUID,
    payload: ApplicationSubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Candidate submits an application to a published job:
    - Pins exact resume version.
    - Prevents duplicates (409 Conflict).
    - Requires candidate profile.
    - Only PUBLISHED jobs accept applications.
    """
    return await submit_application(db, current_user, job_id, payload)


@router.get(
    "/applications/me",
    response_model=PaginatedCandidateApplicationsResponse,
    summary="List candidate's own submitted applications",
)
async def list_my_applications(
    response: Response,
    status: Optional[str] = Query(None, description="Filter by application status"),
    keyword: Optional[str] = Query(None, description="Search by job title"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Page offset"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List authenticated candidate's applications with filtering and pagination."""
    res = await list_candidate_applications(
        db=db,
        candidate_user=current_user,
        status_filter=status,
        keyword=keyword,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(res.total)
    return res


@router.get(
    "/applications/{application_id}",
    response_model=CandidateApplicationResponse,
    summary="Get candidate's application details",
)
async def get_my_application(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get single application details for the authenticated candidate."""
    return await get_candidate_application(db, current_user, application_id)


@router.post(
    "/applications/{application_id}/withdraw",
    response_model=CandidateApplicationResponse,
    summary="Withdraw candidate's own application",
)
async def withdraw_my_application(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Withdraw candidate application:
    - Allowed only from SUBMITTED, UNDER_REVIEW, SHORTLISTED.
    - Preserves application record and creates audit history.
    """
    return await withdraw_candidate_application(db, current_user, application_id)
