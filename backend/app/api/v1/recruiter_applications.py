import uuid
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import (
    get_current_active_user,
    get_org_membership_from_org_id_path,
    require_job_role,
)
from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.user import User
from app.schemas.application import (
    ApplicationStatusUpdateRequest,
    PaginatedRecruiterApplicationsResponse,
    RecruiterApplicationDetailResponse,
)
from app.services.application_service import (
    get_recruiter_application_detail,
    get_submitted_resume_file,
    list_recruiter_applications,
    update_application_status,
)

router = APIRouter()


@router.get(
    "/{organization_id}/jobs/{job_id}/applications",
    response_model=PaginatedRecruiterApplicationsResponse,
    summary="List applications for a specific job in an organization",
)
async def list_job_applications(
    organization_id: uuid.UUID,
    job_id: uuid.UUID,
    response: Response,
    status: Optional[str] = Query(None, description="Filter by status"),
    keyword: Optional[str] = Query(None, description="Search applicant name, email, headline"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Page offset"),
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
    """List applications for a specified job within the organization."""
    res = await list_recruiter_applications(
        db=db,
        organization_id=organization_id,
        job_id=job_id,
        status_filter=status,
        keyword=keyword,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(res.total)
    return res


@router.get(
    "/{organization_id}/applications",
    response_model=PaginatedRecruiterApplicationsResponse,
    summary="List all applications across organization's jobs",
)
async def list_all_organization_applications(
    organization_id: uuid.UUID,
    response: Response,
    job_id: Optional[uuid.UUID] = Query(None, description="Filter by job ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    keyword: Optional[str] = Query(None, description="Search applicant name, email, headline"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Page offset"),
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
    """List all applications belonging to the organization."""
    res = await list_recruiter_applications(
        db=db,
        organization_id=organization_id,
        job_id=job_id,
        status_filter=status,
        keyword=keyword,
        limit=limit,
        offset=offset,
    )
    response.headers["X-Total-Count"] = str(res.total)
    return res


@router.get(
    "/{organization_id}/applications/{application_id}",
    response_model=RecruiterApplicationDetailResponse,
    summary="View detailed application info and status history",
)
async def get_organization_application(
    organization_id: uuid.UUID,
    application_id: uuid.UUID,
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
    """Fetch complete application details including snapshot and audit history."""
    return await get_recruiter_application_detail(db, organization_id, application_id)


@router.patch(
    "/{organization_id}/applications/{application_id}/status",
    response_model=RecruiterApplicationDetailResponse,
    summary="Update application status with lifecycle transition validation",
)
async def patch_application_status(
    organization_id: uuid.UUID,
    application_id: uuid.UUID,
    payload: ApplicationStatusUpdateRequest,
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
    Recruiter updates application status:
    - Enforces allowed lifecycle transitions.
    - Automatically records status update timestamp and history log.
    - VIEWER role cannot update status (403 Forbidden).
    """
    return await update_application_status(
        db=db,
        recruiter_user=current_user,
        organization_id=organization_id,
        application_id=application_id,
        update_in=payload,
    )


@router.get(
    "/{organization_id}/applications/{application_id}/resume",
    summary="Download the exact pinned resume submitted with this application",
)
async def download_application_resume(
    organization_id: uuid.UUID,
    application_id: uuid.UUID,
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
    """
    Stream the exact pinned PDF resume submitted with this application:
    - Validates organization isolation.
    - Does not expose unsubmitted resumes.
    """
    resume, full_path = await get_submitted_resume_file(db, organization_id, application_id)
    return FileResponse(
        path=full_path,
        media_type=resume.mime_type or "application/pdf",
        filename=resume.original_filename,
    )
