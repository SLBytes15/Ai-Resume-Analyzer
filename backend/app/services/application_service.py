import os
import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.application import (
    ALLOWED_CANDIDATE_TRANSITIONS,
    ALLOWED_RECRUITER_TRANSITIONS,
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
)
from app.models.base import utc_now
from app.models.candidate import CandidateProfile, ParsingStatus, Resume
from app.models.job import Job, JobStatus
from app.models.organization import Organization
from app.models.user import User
from app.schemas.application import (
    ApplicationStatusUpdateRequest,
    ApplicationSubmitRequest,
    CandidateApplicationResponse,
    PaginatedCandidateApplicationsResponse,
    PaginatedRecruiterApplicationsResponse,
    RecruiterApplicationDetailResponse,
    RecruiterApplicationListItem,
    StatusHistoryItemResponse,
)
from app.services.storage_service import storage_service


async def submit_application(
    db: AsyncSession,
    candidate_user: User,
    job_id: uuid.UUID,
    submit_in: ApplicationSubmitRequest,
) -> CandidateApplicationResponse:
    """
    Submit a job application as an authenticated candidate:
    - Verifies candidate profile exists.
    - Verifies job exists and is PUBLISHED.
    - Verifies resume belongs to the candidate and parsed successfully.
    - Prevents duplicate applications.
    - Pins exact resume ID.
    - Atomically creates Application and initial ApplicationStatusHistory.
    """
    # 1. Verify candidate profile exists
    cand_stmt = select(CandidateProfile).where(CandidateProfile.user_id == candidate_user.id)
    cand_res = await db.execute(cand_stmt)
    candidate = cand_res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found. Please create a candidate profile before applying.",
        )

    # 2. Verify job exists and is PUBLISHED
    job_stmt = select(Job).options(selectinload(Job.organization)).where(Job.id == job_id)
    job_res = await db.execute(job_stmt)
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if job.status != JobStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not open for applications (current status: {job.status})",
        )

    # 3. Check for existing application (pre-flight check)
    existing_stmt = select(Application).where(
        Application.job_id == job.id,
        Application.candidate_id == candidate.id,
    )
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted an application for this job",
        )

    # 4. Verify resume belongs to candidate and is eligible
    resume_stmt = select(Resume).where(
        Resume.id == submit_in.resume_id,
        Resume.candidate_id == candidate.id,
    )
    resume_res = await db.execute(resume_stmt)
    resume = resume_res.scalar_one_or_none()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found or does not belong to the candidate",
        )
    if resume.parsing_status == ParsingStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected resume failed parsing and is not eligible for application submission",
        )

    # 5. Build candidate snapshot
    snapshot = {
        "candidate_id": str(candidate.id),
        "user_id": str(candidate_user.id),
        "full_name": candidate_user.full_name,
        "email": candidate_user.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "headline": candidate.headline,
        "professional_summary": candidate.professional_summary,
        "resume_id": str(resume.id),
        "resume_filename": resume.original_filename,
        "resume_sha256": resume.sha256,
    }

    now = utc_now()
    application = Application(
        job_id=job.id,
        candidate_id=candidate.id,
        submitted_resume_id=resume.id,
        organization_id=job.organization_id,
        status=ApplicationStatus.SUBMITTED.value,
        cover_letter=submit_in.cover_letter,
        candidate_snapshot=snapshot,
        submitted_at=now,
        status_updated_at=now,
    )
    db.add(application)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted an application for this job",
        )

    # Initial history record
    history = ApplicationStatusHistory(
        application_id=application.id,
        previous_status=None,
        new_status=ApplicationStatus.SUBMITTED.value,
        changed_by=candidate_user.id,
        changed_at=now,
        internal_note="Application submitted by candidate",
    )
    db.add(history)

    await db.commit()
    await db.refresh(application)

    return CandidateApplicationResponse(
        id=application.id,
        job_id=job.id,
        job_title=job.title,
        organization_id=job.organization_id,
        organization_name=job.organization.name if job.organization else "",
        submitted_resume_id=resume.id,
        resume_filename=resume.original_filename,
        status=application.status,
        cover_letter=application.cover_letter,
        submitted_at=application.submitted_at,
        status_updated_at=application.status_updated_at,
        withdrawn_at=application.withdrawn_at,
        job_location=job.location,
        workplace_type=job.workplace_type,
        employment_type=job.employment_type,
    )


async def list_candidate_applications(
    db: AsyncSession,
    candidate_user: User,
    status_filter: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> PaginatedCandidateApplicationsResponse:
    """List applications submitted by the authenticated candidate."""
    cand_stmt = select(CandidateProfile).where(CandidateProfile.user_id == candidate_user.id)
    cand_res = await db.execute(cand_stmt)
    candidate = cand_res.scalar_one_or_none()
    if not candidate:
        return PaginatedCandidateApplicationsResponse(items=[], total=0, limit=limit, offset=offset)

    conditions = [Application.candidate_id == candidate.id]
    if status_filter:
        conditions.append(Application.status == status_filter.upper())
    if keyword:
        conditions.append(Job.title.ilike(f"%{keyword}%"))

    # Count query
    count_stmt = (
        select(func.count(Application.id))
        .join(Job, Application.job_id == Job.id)
        .where(*conditions)
    )
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Data query
    data_stmt = (
        select(Application, Job, Organization, Resume)
        .join(Job, Application.job_id == Job.id)
        .join(Organization, Application.organization_id == Organization.id)
        .join(Resume, Application.submitted_resume_id == Resume.id)
        .where(*conditions)
        .order_by(Application.submitted_at.desc())
        .limit(limit)
        .offset(offset)
    )
    results = await db.execute(data_stmt)

    items: List[CandidateApplicationResponse] = []
    for app_row, job_row, org_row, resume_row in results.all():
        items.append(
            CandidateApplicationResponse(
                id=app_row.id,
                job_id=job_row.id,
                job_title=job_row.title,
                organization_id=org_row.id,
                organization_name=org_row.name,
                submitted_resume_id=resume_row.id,
                resume_filename=resume_row.original_filename,
                status=app_row.status,
                cover_letter=app_row.cover_letter,
                submitted_at=app_row.submitted_at,
                status_updated_at=app_row.status_updated_at,
                withdrawn_at=app_row.withdrawn_at,
                job_location=job_row.location,
                workplace_type=job_row.workplace_type,
                employment_type=job_row.employment_type,
            )
        )

    return PaginatedCandidateApplicationsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_candidate_application(
    db: AsyncSession,
    candidate_user: User,
    application_id: uuid.UUID,
) -> CandidateApplicationResponse:
    """Retrieve details of a specific application for the candidate."""
    cand_stmt = select(CandidateProfile).where(CandidateProfile.user_id == candidate_user.id)
    cand_res = await db.execute(cand_stmt)
    candidate = cand_res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    stmt = (
        select(Application, Job, Organization, Resume)
        .join(Job, Application.job_id == Job.id)
        .join(Organization, Application.organization_id == Organization.id)
        .join(Resume, Application.submitted_resume_id == Resume.id)
        .where(
            Application.id == application_id,
            Application.candidate_id == candidate.id,
        )
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    app_row, job_row, org_row, resume_row = row
    return CandidateApplicationResponse(
        id=app_row.id,
        job_id=job_row.id,
        job_title=job_row.title,
        organization_id=org_row.id,
        organization_name=org_row.name,
        submitted_resume_id=resume_row.id,
        resume_filename=resume_row.original_filename,
        status=app_row.status,
        cover_letter=app_row.cover_letter,
        submitted_at=app_row.submitted_at,
        status_updated_at=app_row.status_updated_at,
        withdrawn_at=app_row.withdrawn_at,
        job_location=job_row.location,
        workplace_type=job_row.workplace_type,
        employment_type=job_row.employment_type,
    )


async def withdraw_candidate_application(
    db: AsyncSession,
    candidate_user: User,
    application_id: uuid.UUID,
) -> CandidateApplicationResponse:
    """Withdraw an existing candidate application."""
    cand_stmt = select(CandidateProfile).where(CandidateProfile.user_id == candidate_user.id)
    cand_res = await db.execute(cand_stmt)
    candidate = cand_res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    stmt = (
        select(Application)
        .options(
            selectinload(Application.job).selectinload(Job.organization),
            selectinload(Application.submitted_resume),
        )
        .where(
            Application.id == application_id,
            Application.candidate_id == candidate.id,
        )
    )
    res = await db.execute(stmt)
    application = res.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.status == ApplicationStatus.WITHDRAWN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application is already withdrawn",
        )

    allowed_from = ALLOWED_CANDIDATE_TRANSITIONS.get(application.status, [])
    if ApplicationStatus.WITHDRAWN.value not in allowed_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot withdraw application in status '{application.status}'",
        )

    now = utc_now()
    prev_status = application.status
    application.status = ApplicationStatus.WITHDRAWN.value
    application.status_updated_at = now
    application.withdrawn_at = now

    history = ApplicationStatusHistory(
        application_id=application.id,
        previous_status=prev_status,
        new_status=ApplicationStatus.WITHDRAWN.value,
        changed_by=candidate_user.id,
        changed_at=now,
        internal_note="Application withdrawn by candidate",
    )
    db.add(history)

    await db.commit()
    await db.refresh(application)

    return CandidateApplicationResponse(
        id=application.id,
        job_id=application.job.id,
        job_title=application.job.title,
        organization_id=application.organization_id,
        organization_name=application.job.organization.name if application.job.organization else "",
        submitted_resume_id=application.submitted_resume.id,
        resume_filename=application.submitted_resume.original_filename,
        status=application.status,
        cover_letter=application.cover_letter,
        submitted_at=application.submitted_at,
        status_updated_at=application.status_updated_at,
        withdrawn_at=application.withdrawn_at,
        job_location=application.job.location,
        workplace_type=application.job.workplace_type,
        employment_type=application.job.employment_type,
    )


# ---------------------------------------------------------------------------
# Recruiter Application Operations
# ---------------------------------------------------------------------------


async def list_recruiter_applications(
    db: AsyncSession,
    organization_id: uuid.UUID,
    job_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> PaginatedRecruiterApplicationsResponse:
    """List applications for an organization, optionally filtered by job_id, status, keyword."""
    conditions = [Application.organization_id == organization_id]
    if job_id:
        conditions.append(Application.job_id == job_id)
    if status_filter:
        conditions.append(Application.status == status_filter.upper())
    if keyword:
        kw = f"%{keyword}%"
        conditions.append(
            or_(
                Job.title.ilike(kw),
                User.full_name.ilike(kw),
                User.email.ilike(kw),
                CandidateProfile.headline.ilike(kw),
            )
        )

    # Count query
    count_stmt = (
        select(func.count(Application.id))
        .join(Job, Application.job_id == Job.id)
        .join(CandidateProfile, Application.candidate_id == CandidateProfile.id)
        .join(User, CandidateProfile.user_id == User.id)
        .where(*conditions)
    )
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Data query
    data_stmt = (
        select(Application, Job, CandidateProfile, User, Resume)
        .join(Job, Application.job_id == Job.id)
        .join(CandidateProfile, Application.candidate_id == CandidateProfile.id)
        .join(User, CandidateProfile.user_id == User.id)
        .join(Resume, Application.submitted_resume_id == Resume.id)
        .where(*conditions)
        .order_by(Application.submitted_at.desc())
        .limit(limit)
        .offset(offset)
    )
    results = await db.execute(data_stmt)

    items: List[RecruiterApplicationListItem] = []
    for app_row, job_row, cand_row, user_row, resume_row in results.all():
        snapshot = app_row.candidate_snapshot or {}
        items.append(
            RecruiterApplicationListItem(
                id=app_row.id,
                job_id=job_row.id,
                job_title=job_row.title,
                organization_id=app_row.organization_id,
                candidate_id=cand_row.id,
                candidate_name=snapshot.get("full_name") or user_row.full_name,
                candidate_email=snapshot.get("email") or user_row.email,
                candidate_headline=snapshot.get("headline") or cand_row.headline,
                submitted_resume_id=resume_row.id,
                resume_filename=resume_row.original_filename,
                status=app_row.status,
                submitted_at=app_row.submitted_at,
                status_updated_at=app_row.status_updated_at,
                withdrawn_at=app_row.withdrawn_at,
                cover_letter=app_row.cover_letter,
            )
        )

    return PaginatedRecruiterApplicationsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_recruiter_application_detail(
    db: AsyncSession,
    organization_id: uuid.UUID,
    application_id: uuid.UUID,
) -> RecruiterApplicationDetailResponse:
    """Fetch complete application details for recruiter including snapshot & status history."""
    stmt = (
        select(Application)
        .options(
            selectinload(Application.job),
            selectinload(Application.candidate).selectinload(CandidateProfile.user),
            selectinload(Application.submitted_resume),
            selectinload(Application.status_history),
        )
        .where(
            Application.id == application_id,
            Application.organization_id == organization_id,
        )
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    snapshot = app.candidate_snapshot or {}
    user_name = snapshot.get("full_name") or (app.candidate.user.full_name if app.candidate and app.candidate.user else None)
    user_email = snapshot.get("email") or (app.candidate.user.email if app.candidate and app.candidate.user else None)
    headline = snapshot.get("headline") or (app.candidate.headline if app.candidate else None)

    history_items = [
        StatusHistoryItemResponse(
            id=h.id,
            previous_status=h.previous_status,
            new_status=h.new_status,
            changed_by=h.changed_by,
            changed_at=h.changed_at,
            internal_note=h.internal_note,
        )
        for h in sorted(app.status_history, key=lambda x: x.changed_at)
    ]

    return RecruiterApplicationDetailResponse(
        id=app.id,
        job_id=app.job_id,
        job_title=app.job.title if app.job else "",
        organization_id=app.organization_id,
        candidate_id=app.candidate_id,
        candidate_name=user_name,
        candidate_email=user_email,
        candidate_headline=headline,
        submitted_resume_id=app.submitted_resume_id,
        resume_filename=app.submitted_resume.original_filename if app.submitted_resume else "",
        status=app.status,
        submitted_at=app.submitted_at,
        status_updated_at=app.status_updated_at,
        withdrawn_at=app.withdrawn_at,
        cover_letter=app.cover_letter,
        candidate_snapshot=app.candidate_snapshot,
        status_history=history_items,
    )


async def update_application_status(
    db: AsyncSession,
    recruiter_user: User,
    organization_id: uuid.UUID,
    application_id: uuid.UUID,
    update_in: ApplicationStatusUpdateRequest,
) -> RecruiterApplicationDetailResponse:
    """Update application status with lifecycle transition validation and history logging."""
    stmt = (
        select(Application)
        .options(
            selectinload(Application.job),
            selectinload(Application.candidate).selectinload(CandidateProfile.user),
            selectinload(Application.submitted_resume),
            selectinload(Application.status_history),
        )
        .where(
            Application.id == application_id,
            Application.organization_id == organization_id,
        )
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    target_status = update_in.status.value
    if target_status == ApplicationStatus.WITHDRAWN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recruiters cannot mark an application as WITHDRAWN",
        )

    allowed_transitions = ALLOWED_RECRUITER_TRANSITIONS.get(app.status, [])
    if target_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{app.status}' to '{target_status}'. Allowed: {allowed_transitions}",
        )

    now = utc_now()
    prev_status = app.status
    app.status = target_status
    app.status_updated_at = now

    history = ApplicationStatusHistory(
        application_id=app.id,
        previous_status=prev_status,
        new_status=target_status,
        changed_by=recruiter_user.id,
        changed_at=now,
        internal_note=update_in.internal_note,
    )
    db.add(history)

    await db.commit()
    await db.refresh(app)

    return await get_recruiter_application_detail(db, organization_id, application_id)


async def get_submitted_resume_file(
    db: AsyncSession,
    organization_id: uuid.UUID,
    application_id: uuid.UUID,
) -> Tuple[Resume, str]:
    """
    Validate recruiter access to the exact pinned resume submitted with an application.
    Returns the Resume record and the absolute path to the stored PDF file.
    """
    stmt = select(Application).where(
        Application.id == application_id,
        Application.organization_id == organization_id,
    )
    res = await db.execute(stmt)
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    resume_stmt = select(Resume).where(
        Resume.id == app.submitted_resume_id,
        Resume.candidate_id == app.candidate_id,
    )
    resume_res = await db.execute(resume_stmt)
    resume = resume_res.scalar_one_or_none()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submitted resume file record not found",
        )

    abs_path = storage_service.get_absolute_path(resume.storage_path)
    if not abs_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found on disk",
        )

    return resume, str(abs_path)
