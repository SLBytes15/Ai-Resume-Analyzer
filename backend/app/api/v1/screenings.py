import uuid
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_active_user,
    require_job_role,
)
from app.core.database import get_db
from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.user import User
from app.schemas.screening import (
    PaginatedScreeningResultsResponse,
    PaginatedScreeningRunsResponse,
    ScreeningInsightResponse,
    ScreeningResultDetailResponse,
    ScreeningRunResponse,
    ScreeningTriggerRequest,
)
from app.services.screening_service import (
    get_screening_result_detail,
    get_screening_run_detail,
    list_job_screening_runs,
    list_screening_results,
    retry_candidate_insight,
    trigger_screening_run,
)

router = APIRouter()


@router.post(
    "/{organization_id}/jobs/{job_id}/screenings",
    response_model=ScreeningRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger an AI screening run for all applications of a job",
)
async def create_job_screening(
    organization_id: uuid.UUID,
    job_id: uuid.UUID,
    payload: ScreeningTriggerRequest = ScreeningTriggerRequest(),
    current_user: User = Depends(get_current_active_user),
    org_membership: Tuple[Organization, OrganizationMembership] = Depends(
        require_job_role([
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
            OrganizationRole.RECRUITER,
        ])
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger automated screening run:
    - OWNER, ADMIN, RECRUITER authorized (VIEWER is 403 Forbidden).
    - Processes applications sequentially using pinned resume versions.
    - Deterministic scoring, grounded explainability, and auditability.
    """
    return await trigger_screening_run(
        db=db,
        recruiter_user=current_user,
        organization_id=organization_id,
        job_id=job_id,
        trigger_in=payload,
    )


@router.get(
    "/{organization_id}/jobs/{job_id}/screenings",
    response_model=PaginatedScreeningRunsResponse,
    summary="List all historical screening runs for a job",
)
async def list_job_screenings(
    organization_id: uuid.UUID,
    job_id: uuid.UUID,
    response: Response,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    org_membership: Tuple[Organization, OrganizationMembership] = Depends(
        require_job_role([
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
            OrganizationRole.RECRUITER,
            OrganizationRole.VIEWER,
        ])
    ),
    db: AsyncSession = Depends(get_db),
):
    """List historical screening runs for a job within the organization."""
    res = await list_job_screening_runs(
        db=db,
        organization_id=organization_id,
        job_id=job_id,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(res.total)
    return res


@router.get(
    "/{organization_id}/screenings/{run_id}",
    response_model=ScreeningRunResponse,
    summary="Get status and details of a screening run",
)
async def get_screening_run(
    organization_id: uuid.UUID,
    run_id: uuid.UUID,
    org_membership: Tuple[Organization, OrganizationMembership] = Depends(
        require_job_role([
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
            OrganizationRole.RECRUITER,
            OrganizationRole.VIEWER,
        ])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Fetch details of a single screening run."""
    return await get_screening_run_detail(
        db=db,
        organization_id=organization_id,
        run_id=run_id,
    )


@router.get(
    "/{organization_id}/screenings/{run_id}/results",
    response_model=PaginatedScreeningResultsResponse,
    summary="List candidate screening results for a run ranked by score",
)
async def list_run_results(
    organization_id: uuid.UUID,
    run_id: uuid.UUID,
    response: Response,
    status: Optional[str] = Query(None, description="Filter by status (COMPLETED, FAILED)"),
    score_min: Optional[float] = Query(None, ge=0, le=100, description="Minimum total score"),
    score_max: Optional[float] = Query(None, ge=0, le=100, description="Maximum total score"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    org_membership: Tuple[Organization, OrganizationMembership] = Depends(
        require_job_role([
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
            OrganizationRole.RECRUITER,
            OrganizationRole.VIEWER,
        ])
    ),
    db: AsyncSession = Depends(get_db),
):
    """List ranked candidate screening results for a run with score filters and pagination."""
    res = await list_screening_results(
        db=db,
        organization_id=organization_id,
        run_id=run_id,
        status_filter=status,
        score_min=score_min,
        score_max=score_max,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(res.total)
    return res


@router.get(
    "/{organization_id}/screenings/results/{result_id}",
    response_model=ScreeningResultDetailResponse,
    summary="Get complete details, evidence breakdown, and explanation for a candidate result",
)
async def get_screening_result(
    organization_id: uuid.UUID,
    result_id: uuid.UUID,
    org_membership: Tuple[Organization, OrganizationMembership] = Depends(
        require_job_role([
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
            OrganizationRole.RECRUITER,
            OrganizationRole.VIEWER,
        ])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full screening result details including matched evidence and scoring breakdown."""
    return await get_screening_result_detail(
        db=db,
        organization_id=organization_id,
        result_id=result_id,
    )


@router.post(
    "/{organization_id}/screenings/results/{result_id}/insight/retry",
    response_model=ScreeningInsightResponse,
    summary="Retry candidate insight generation without modifying screening score",
)
async def retry_screening_result_insight(
    organization_id: uuid.UUID,
    result_id: uuid.UUID,
    org_membership: Tuple[Organization, OrganizationMembership] = Depends(
        require_job_role([
            OrganizationRole.OWNER,
            OrganizationRole.ADMIN,
            OrganizationRole.RECRUITER,
        ])
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually retry generating explainable candidate insights:
    - Retains existing score and evidence.
    - Never modifies total score, component scores, or rankings.
    """
    return await retry_candidate_insight(
        db=db,
        organization_id=organization_id,
        result_id=result_id,
    )
