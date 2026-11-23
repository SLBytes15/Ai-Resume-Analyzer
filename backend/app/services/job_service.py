import re
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.base import utc_now
from app.models.job import EmploymentType, Job, JobStatus, WorkplaceType
from app.models.organization import Organization
from app.schemas.job import JobCreate, JobUpdate


def generate_slug(title: str) -> str:
    """Generate a URL-friendly slug with unique entropy."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()[:40]
    suffix = uuid.uuid4().hex[:6]
    return f"{clean}-{suffix}" if clean else suffix


async def create_job(
    db: AsyncSession,
    organization_id: uuid.UUID,
    created_by: Optional[uuid.UUID],
    job_in: JobCreate,
) -> Job:
    """Create a new job in DRAFT status belonging to organization_id."""
    slug_val = job_in.slug or generate_slug(job_in.title)

    job = Job(
        organization_id=organization_id,
        created_by=created_by,
        title=job_in.title,
        slug=slug_val,
        department=job_in.department,
        description=job_in.description,
        responsibilities=job_in.responsibilities,
        qualifications=job_in.qualifications,
        location=job_in.location,
        workplace_type=job_in.workplace_type.value,
        employment_type=job_in.employment_type.value,
        experience_min=job_in.experience_min,
        experience_max=job_in.experience_max,
        salary_min=job_in.salary_min,
        salary_max=job_in.salary_max,
        salary_currency=job_in.salary_currency or "INR",
        required_skills=job_in.required_skills,
        preferred_skills=job_in.preferred_skills,
        status=JobStatus.DRAFT.value,
        published_at=None,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_job_by_id(
    db: AsyncSession,
    job_id: uuid.UUID,
    organization_id: Optional[uuid.UUID] = None,
) -> Optional[Job]:
    """Retrieve an organization job by ID, optionally validating organization isolation."""
    query = select(Job).options(selectinload(Job.organization)).where(Job.id == job_id)
    if organization_id is not None:
        query = query.where(Job.organization_id == organization_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_public_job_by_id(
    db: AsyncSession,
    job_id: uuid.UUID,
) -> Optional[Job]:
    """Retrieve public job details. Only PUBLISHED jobs with active organizations are returned."""
    query = (
        select(Job)
        .join(Organization, Job.organization_id == Organization.id)
        .options(selectinload(Job.organization))
        .where(
            Job.id == job_id,
            Job.status == JobStatus.PUBLISHED.value,
            Organization.is_active.is_(True),
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_job(
    db: AsyncSession,
    job: Job,
    job_in: JobUpdate,
) -> Job:
    """Update permitted fields of an existing job."""
    if job.status == JobStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot modify an archived job",
        )

    update_data = job_in.model_dump(exclude_unset=True)

    # Validate combined experience bounds
    new_exp_min = update_data.get("experience_min", job.experience_min)
    new_exp_max = update_data.get("experience_max", job.experience_max)
    if new_exp_min is not None and new_exp_max is not None:
        if new_exp_min > new_exp_max:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="experience_min cannot be greater than experience_max",
            )

    # Validate combined salary bounds
    new_sal_min = update_data.get("salary_min", job.salary_min)
    new_sal_max = update_data.get("salary_max", job.salary_max)
    if new_sal_min is not None and new_sal_max is not None:
        if new_sal_min > new_sal_max:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="salary_min cannot be greater than salary_max",
            )

    # Validate combined skill overlap
    new_req = update_data.get("required_skills", job.required_skills) or []
    new_pref = update_data.get("preferred_skills", job.preferred_skills) or []
    req_set = {s.strip().lower() for s in new_req if s}
    for p in new_pref:
        if p and p.strip().lower() in req_set:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Skill '{p.strip()}' cannot appear in both required and preferred skills",
            )

    for field, value in update_data.items():
        if field in ("workplace_type", "employment_type") and hasattr(value, "value"):
            setattr(job, field, value.value)
        else:
            setattr(job, field, value)

    # Preserve original published_at when editing
    job.updated_at = utc_now()
    await db.commit()
    await db.refresh(job)
    return job


async def publish_job(db: AsyncSession, job: Job) -> Job:
    """Transition a DRAFT job to PUBLISHED."""
    if job.status == JobStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is already published",
        )
    if job.status in (JobStatus.CLOSED.value, JobStatus.ARCHIVED.value):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot publish job in status {job.status}. Invalid state transition.",
        )
    if job.status != JobStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid state transition from {job.status} to PUBLISHED",
        )

    job.status = JobStatus.PUBLISHED.value
    if job.published_at is None:
        job.published_at = utc_now()
    job.updated_at = utc_now()

    await db.commit()
    await db.refresh(job)
    return job


async def close_job(db: AsyncSession, job: Job) -> Job:
    """Transition a PUBLISHED job to CLOSED."""
    if job.status == JobStatus.CLOSED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is already closed",
        )
    if job.status == JobStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot close a draft job. It must be published first.",
        )
    if job.status == JobStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot close an archived job",
        )
    if job.status != JobStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid state transition from {job.status} to CLOSED",
        )

    job.status = JobStatus.CLOSED.value
    job.updated_at = utc_now()

    await db.commit()
    await db.refresh(job)
    return job


async def archive_job(db: AsyncSession, job: Job) -> Job:
    """Transition a job to ARCHIVED. DRAFT jobs cannot be archived directly."""
    if job.status == JobStatus.ARCHIVED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is already archived",
        )
    if job.status == JobStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot archive a draft job. Invalid state transition.",
        )

    job.status = JobStatus.ARCHIVED.value
    job.updated_at = utc_now()

    await db.commit()
    await db.refresh(job)
    return job


async def list_organization_jobs(
    db: AsyncSession,
    organization_id: uuid.UUID,
    status_filter: Optional[str] = None,
    employment_type: Optional[str] = None,
    workplace_type: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Job], int]:
    """List jobs for an organization with optional filters, count, and pagination."""
    conditions = [Job.organization_id == organization_id]

    if status_filter:
        conditions.append(Job.status == status_filter)
    if employment_type:
        conditions.append(Job.employment_type == employment_type)
    if workplace_type:
        conditions.append(Job.workplace_type == workplace_type)
    if keyword and keyword.strip():
        kw_pattern = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                Job.title.ilike(kw_pattern),
                Job.department.ilike(kw_pattern),
                Job.description.ilike(kw_pattern),
            )
        )

    count_query = select(func.count(Job.id)).where(*conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    data_query = (
        select(Job)
        .where(*conditions)
        .order_by(Job.created_at.desc(), Job.id.desc())
        .offset(offset)
        .limit(limit)
    )
    data_result = await db.execute(data_query)
    jobs = list(data_result.scalars().all())

    return jobs, total


async def list_public_jobs(
    db: AsyncSession,
    keyword: Optional[str] = None,
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    workplace_type: Optional[str] = None,
    skill: Optional[str] = None,
    sort: str = "newest",
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[Job], int]:
    """
    List only PUBLISHED jobs from active organizations with filters, sorting, and pagination.
    Does not expose draft, closed, or archived jobs.
    """
    conditions = [
        Job.status == JobStatus.PUBLISHED.value,
        Organization.is_active.is_(True),
    ]

    if keyword and keyword.strip():
        kw_pattern = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                Job.title.ilike(kw_pattern),
                Job.department.ilike(kw_pattern),
                Job.description.ilike(kw_pattern),
            )
        )
    if location and location.strip():
        conditions.append(Job.location.ilike(f"%{location.strip()}%"))
    if employment_type:
        conditions.append(Job.employment_type == employment_type)
    if workplace_type:
        conditions.append(Job.workplace_type == workplace_type)
    if skill and skill.strip():
        skill_clean = f"%{skill.strip()}%"
        conditions.append(
            text(
                "EXISTS (SELECT 1 FROM jsonb_array_elements_text(jobs.required_skills) elem WHERE elem ILIKE :skill_param)"
            ).bindparams(skill_param=skill_clean)
        )

    count_query = (
        select(func.count(Job.id))
        .join(Organization, Job.organization_id == Organization.id)
        .where(*conditions)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    order_clause = (
        (Job.published_at.asc(), Job.id.asc())
        if sort == "oldest"
        else (Job.published_at.desc(), Job.id.desc())
    )

    data_query = (
        select(Job)
        .join(Organization, Job.organization_id == Organization.id)
        .options(selectinload(Job.organization))
        .where(*conditions)
        .order_by(*order_clause)
        .offset(offset)
        .limit(limit)
    )
    data_result = await db.execute(data_query)
    jobs = list(data_result.scalars().all())

    return jobs, total
