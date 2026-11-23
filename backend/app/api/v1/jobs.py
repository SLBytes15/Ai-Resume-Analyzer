import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_current_active_user,
    get_org_membership_from_org_id_path,
    require_job_role,
)
from app.core.database import get_db
from app.models.organization import OrganizationRole
from app.models.user import User
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.services.job_service import (
    archive_job,
    close_job,
    create_job,
    get_job_by_id,
    list_organization_jobs,
    publish_job,
    update_job,
)

router = APIRouter()


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft job",
)
async def create_new_draft_job(
    organization_id: uuid.UUID = Path(..., description="Organization ID"),
    job_in: JobCreate = ...,
    org_and_membership=Depends(
        require_job_role(
            [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.RECRUITER]
        )
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Create a new job for the organization. Initial status is always DRAFT."""
    org, _ = org_and_membership
    job = await create_job(
        db,
        organization_id=org.id,
        created_by=current_user.id,
        job_in=job_in,
    )
    return job


@router.get(
    "",
    response_model=List[JobResponse],
    status_code=status.HTTP_200_OK,
    summary="List organization jobs",
)
async def list_jobs_for_organization(
    response: Response,
    organization_id: uuid.UUID = Path(..., description="Organization ID"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, PUBLISHED, CLOSED, ARCHIVED)"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type"),
    workplace_type: Optional[str] = Query(None, description="Filter by workplace type"),
    keyword: Optional[str] = Query(None, description="Search keyword in title, department, description"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    org_and_membership=Depends(get_org_membership_from_org_id_path),
    db: AsyncSession = Depends(get_db),
) -> List[JobResponse]:
    """List all jobs belonging to the organization. Accessible to all org members."""
    org, _ = org_and_membership
    jobs, total = await list_organization_jobs(
        db,
        organization_id=org.id,
        status_filter=status,
        employment_type=employment_type,
        workplace_type=workplace_type,
        keyword=keyword,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)
    return jobs


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve an organization job",
)
async def get_organization_job(
    organization_id: uuid.UUID = Path(..., description="Organization ID"),
    job_id: uuid.UUID = Path(..., description="Job ID"),
    org_and_membership=Depends(get_org_membership_from_org_id_path),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Retrieve details for a specific organization job. Ensures organization isolation."""
    org, _ = org_and_membership
    job = await get_job_by_id(db, job_id=job_id, organization_id=org.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found in this organization",
        )
    return job


@router.patch(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Update organization job fields",
)
async def update_organization_job(
    organization_id: uuid.UUID = Path(..., description="Organization ID"),
    job_id: uuid.UUID = Path(..., description="Job ID"),
    job_in: JobUpdate = ...,
    org_and_membership=Depends(
        require_job_role(
            [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.RECRUITER]
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Update permitted job fields. Status cannot be modified directly via PATCH."""
    org, _ = org_and_membership
    job = await get_job_by_id(db, job_id=job_id, organization_id=org.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found in this organization",
        )
    return await update_job(db, job=job, job_in=job_in)


@router.post(
    "/{job_id}/publish",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish a draft job",
)
async def publish_organization_job(
    organization_id: uuid.UUID = Path(..., description="Organization ID"),
    job_id: uuid.UUID = Path(..., description="Job ID"),
    org_and_membership=Depends(
        require_job_role(
            [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.RECRUITER]
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Publish a draft job, setting published_at timestamp."""
    org, _ = org_and_membership
    job = await get_job_by_id(db, job_id=job_id, organization_id=org.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found in this organization",
        )
    return await publish_job(db, job=job)


@router.post(
    "/{job_id}/close",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Close a published job",
)
async def close_organization_job(
    organization_id: uuid.UUID = Path(..., description="Organization ID"),
    job_id: uuid.UUID = Path(..., description="Job ID"),
    org_and_membership=Depends(
        require_job_role(
            [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.RECRUITER]
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Close a published job, removing it from candidate-facing listings."""
    org, _ = org_and_membership
    job = await get_job_by_id(db, job_id=job_id, organization_id=org.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found in this organization",
        )
    return await close_job(db, job=job)


@router.post(
    "/{job_id}/archive",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive a job",
)
async def archive_organization_job(
    organization_id: uuid.UUID = Path(..., description="Organization ID"),
    job_id: uuid.UUID = Path(..., description="Job ID"),
    org_and_membership=Depends(
        require_job_role(
            [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.RECRUITER]
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Archive a job for historical reference. Must not be DRAFT."""
    org, _ = org_and_membership
    job = await get_job_by_id(db, job_id=job_id, organization_id=org.id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found in this organization",
        )
    return await archive_job(db, job=job)
