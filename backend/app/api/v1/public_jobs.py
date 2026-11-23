import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.job import PublicJobResponse
from app.services.job_service import get_public_job_by_id, list_public_jobs

router = APIRouter()


@router.get(
    "",
    response_model=List[PublicJobResponse],
    status_code=status.HTTP_200_OK,
    summary="List published jobs",
)
async def list_published_jobs(
    response: Response,
    keyword: Optional[str] = Query(None, description="Search keyword in title, department, or description"),
    location: Optional[str] = Query(None, description="Filter by location"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type"),
    workplace_type: Optional[str] = Query(None, description="Filter by workplace type"),
    skill: Optional[str] = Query(None, description="Filter by required skill"),
    sort: str = Query("newest", pattern="^(newest|oldest)$", description="Sort by publication date (newest/oldest)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> List[PublicJobResponse]:
    """
    Publicly list only PUBLISHED jobs from active organizations.
    Draft, closed, and archived jobs are never exposed.
    """
    jobs, total = await list_public_jobs(
        db,
        keyword=keyword,
        location=location,
        employment_type=employment_type,
        workplace_type=workplace_type,
        skill=skill,
        sort=sort,
        limit=limit,
        offset=offset,
    )

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)

    return [
        PublicJobResponse(
            id=j.id,
            title=j.title,
            slug=j.slug,
            organization_name=j.organization.name if j.organization else "",
            department=j.department,
            description=j.description,
            responsibilities=j.responsibilities,
            qualifications=j.qualifications,
            location=j.location,
            workplace_type=j.workplace_type,
            employment_type=j.employment_type,
            experience_min=j.experience_min,
            experience_max=j.experience_max,
            salary_min=float(j.salary_min) if j.salary_min is not None else None,
            salary_max=float(j.salary_max) if j.salary_max is not None else None,
            salary_currency=j.salary_currency,
            required_skills=j.required_skills,
            preferred_skills=j.preferred_skills,
            published_at=j.published_at,
            created_at=j.created_at,
        )
        for j in jobs
    ]


@router.get(
    "/{job_id}",
    response_model=PublicJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public job details",
)
async def get_published_job(
    job_id: uuid.UUID = Path(..., description="Job ID"),
    db: AsyncSession = Depends(get_db),
) -> PublicJobResponse:
    """
    Retrieve public details of a single PUBLISHED job.
    Returns 404 if the job is draft, closed, archived, or not found.
    """
    job = await get_public_job_by_id(db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or not publicly available",
        )

    return PublicJobResponse(
        id=job.id,
        title=job.title,
        slug=job.slug,
        organization_name=job.organization.name if job.organization else "",
        department=job.department,
        description=job.description,
        responsibilities=job.responsibilities,
        qualifications=job.qualifications,
        location=job.location,
        workplace_type=job.workplace_type,
        employment_type=job.employment_type,
        experience_min=job.experience_min,
        experience_max=job.experience_max,
        salary_min=float(job.salary_min) if job.salary_min is not None else None,
        salary_max=float(job.salary_max) if job.salary_max is not None else None,
        salary_currency=job.salary_currency,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        published_at=job.published_at,
        created_at=job.created_at,
    )
