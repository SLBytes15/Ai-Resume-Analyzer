import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.application import Application
from app.models.base import utc_now
from app.models.candidate import CandidateProfile, Resume
from app.models.job import Job
from app.models.screening import (
    ScreeningInsight,
    ScreeningInsightStatus,
    ScreeningResult,
    ScreeningResultStatus,
    ScreeningRun,
    ScreeningRunStatus,
)
from app.models.user import User
from app.schemas.screening import (
    PaginatedScreeningResultsResponse,
    PaginatedScreeningRunsResponse,
    ScreeningInsightResponse,
    ScreeningResultDetailResponse,
    ScreeningResultListItem,
    ScreeningRunResponse,
    ScreeningTriggerRequest,
)
from app.services.candidate_insight_generator import (
    INSIGHT_PROMPT_VERSION,
    candidate_insight_generator,
)
from app.services.evidence_extractor import evidence_extractor
from app.services.pdf_extractor import pdf_extractor
from app.services.scoring_engine import ScoringEngine, scoring_engine
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)


async def trigger_screening_run(
    db: AsyncSession,
    recruiter_user: User,
    organization_id: uuid.UUID,
    job_id: uuid.UUID,
    trigger_in: ScreeningTriggerRequest,
) -> ScreeningRunResponse:
    """
    Trigger in-process sequential screening for applications of a job:
    1. Validates job belongs to organization.
    2. Protects against concurrent active runs on the same job.
    3. Retrieves eligible applications.
    4. Extracts evidence from each application's exact pinned resume.
    5. Calculates deterministic scores and explanations.
    6. Persists run and results atomically.
    """
    # 1. Verify job exists and belongs to the organization
    job_stmt = select(Job).where(
        Job.id == job_id,
        Job.organization_id == organization_id,
    )
    job_res = await db.execute(job_stmt)
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found in this organization",
        )

    # 2. Concurrency protection: prevent simultaneous runs for the same job
    active_run_stmt = select(ScreeningRun).where(
        ScreeningRun.job_id == job.id,
        ScreeningRun.status == ScreeningRunStatus.PROCESSING.value,
    )
    active_run_res = await db.execute(active_run_stmt)
    if active_run_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A screening run is currently in progress for this job. Please wait for it to complete.",
        )

    # 3. Build snapshot of target job criteria
    job_snapshot = {
        "job_id": str(job.id),
        "title": job.title,
        "department": job.department,
        "description": job.description,
        "responsibilities": job.responsibilities,
        "qualifications": job.qualifications,
        "location": job.location,
        "workplace_type": job.workplace_type,
        "employment_type": job.employment_type,
        "experience_min": job.experience_min,
        "experience_max": job.experience_max,
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
    }

    # 4. Configure custom or default weights
    engine = (
        ScoringEngine(trigger_in.scoring_weights)
        if trigger_in.scoring_weights
        else scoring_engine
    )

    now = utc_now()
    screening_run = ScreeningRun(
        organization_id=organization_id,
        job_id=job.id,
        triggered_by=recruiter_user.id,
        status=ScreeningRunStatus.PROCESSING.value,
        total_applications=0,
        processed_applications=0,
        failed_applications=0,
        scoring_config=engine.get_scoring_config(),
        job_snapshot=job_snapshot,
        started_at=now,
    )
    db.add(screening_run)
    await db.commit()
    await db.refresh(screening_run)

    # 5. Retrieve applications for this job
    apps_stmt = (
        select(Application)
        .options(
            selectinload(Application.submitted_resume),
            selectinload(Application.candidate).selectinload(CandidateProfile.user),
        )
        .where(
            Application.job_id == job.id,
            Application.organization_id == organization_id,
        )
        .order_by(Application.submitted_at.asc())
    )
    apps_res = await db.execute(apps_stmt)
    applications = apps_res.scalars().all()

    screening_run.total_applications = len(applications)

    if len(applications) == 0:
        screening_run.status = ScreeningRunStatus.COMPLETED.value
        screening_run.completed_at = utc_now()
        await db.commit()
        await db.refresh(screening_run)
        return ScreeningRunResponse.model_validate(screening_run)

    # 6. Process applications sequentially
    processed_count = 0
    failed_count = 0
    error_messages = []

    for app in applications:
        try:
            resume = app.submitted_resume
            if not resume:
                # Attempt to query resume directly
                r_stmt = select(Resume).where(Resume.id == app.submitted_resume_id)
                r_res = await db.execute(r_stmt)
                resume = r_res.scalar_one_or_none()

            if not resume:
                raise ValueError("Submitted resume record does not exist")

            # Resolve resume text
            resume_text = resume.extracted_text
            if not resume_text:
                abs_path = storage_service.get_absolute_path(resume.storage_path)
                if abs_path.exists():
                    with open(abs_path, "rb") as f:
                        file_bytes = f.read()
                    resume_text = pdf_extractor.extract_text(file_bytes)
                else:
                    resume_text = ""

            # Extract evidence
            evidence = await evidence_extractor.extract_evidence(
                job_criteria=job_snapshot,
                resume_text=resume_text or "No text available",
                parsed_data=resume.parsed_data,
            )

            # Calculate deterministic scores
            ev_dict = evidence.model_dump()
            score_data = engine.calculate_screening_score(
                required_skills=job.required_skills or [],
                preferred_skills=job.preferred_skills or [],
                experience_min=job.experience_min,
                experience_max=job.experience_max,
                evidenced_skills=ev_dict.get("skills", []),
                extracted_experience=ev_dict.get("experience", []),
                extracted_projects=ev_dict.get("projects", []),
            )

            # Persist screening result
            result_item = ScreeningResult(
                screening_run_id=screening_run.id,
                application_id=app.id,
                organization_id=organization_id,
                job_id=job.id,
                candidate_id=app.candidate_id,
                submitted_resume_id=resume.id,
                resume_sha256=resume.sha256,
                total_score=score_data["total_score"],
                required_skill_score=score_data["required_skill_score"],
                preferred_skill_score=score_data["preferred_skill_score"],
                experience_score=score_data["experience_score"],
                matched_skills=score_data["matched_skills"],
                missing_evidence=score_data["missing_evidence"],
                preferred_skill_matches=score_data["preferred_skill_matches"],
                experience_assessment=score_data["experience_assessment"],
                evidence_items=ev_dict.get("skills", []),
                explanation=score_data["explanation"],
                confidence_level=score_data["confidence_level"],
                processing_status=ScreeningResultStatus.COMPLETED.value,
            )
            db.add(result_item)
            await db.flush()

            # Generate candidate insight ("Why this score?")
            try:
                insight_schema, model_used, is_fallback = await candidate_insight_generator.generate_insight(
                    job_criteria=job_snapshot,
                    score_data=score_data,
                    extracted_projects=ev_dict.get("projects", []),
                    extracted_experience=ev_dict.get("experience", []),
                    resume_text=resume_text,
                )
                insight_status = (
                    ScreeningInsightStatus.COMPLETED.value
                    if not is_fallback
                    else ScreeningInsightStatus.COMPLETED.value
                )
                insight_record = ScreeningInsight(
                    screening_result_id=result_item.id,
                    screening_run_id=screening_run.id,
                    application_id=app.id,
                    status=insight_status,
                    model_id=model_used,
                    prompt_version=INSIGHT_PROMPT_VERSION,
                    insight_data=insight_schema.model_dump(),
                )
                db.add(insight_record)
                await db.flush()
            except Exception as e_insight:
                logger.warning(
                    f"Candidate insight generation failed for result {result_item.id}: {e_insight}. Storing deterministic fallback."
                )
                fallback_schema = candidate_insight_generator.generate_deterministic_fallback(
                    job_criteria=job_snapshot,
                    score_data=score_data,
                    extracted_projects=ev_dict.get("projects", []),
                    extracted_experience=ev_dict.get("experience", []),
                )
                failed_insight = ScreeningInsight(
                    screening_result_id=result_item.id,
                    screening_run_id=screening_run.id,
                    application_id=app.id,
                    status=ScreeningInsightStatus.FAILED.value,
                    model_id="deterministic-fallback",
                    prompt_version=INSIGHT_PROMPT_VERSION,
                    insight_data=fallback_schema.model_dump(),
                    error_message=str(e_insight),
                )
                db.add(failed_insight)
                await db.flush()

            processed_count += 1

        except Exception as e:
            logger.error(f"Error screening application {app.id}: {e}", exc_info=True)
            failed_count += 1
            error_messages.append(f"App {app.id}: {str(e)}")

            failed_result = ScreeningResult(
                screening_run_id=screening_run.id,
                application_id=app.id,
                organization_id=organization_id,
                job_id=job.id,
                candidate_id=app.candidate_id,
                submitted_resume_id=app.submitted_resume_id,
                resume_sha256=getattr(app.submitted_resume, "sha256", "UNKNOWN"),
                total_score=None,
                matched_skills=[],
                missing_evidence=[],
                preferred_skill_matches=[],
                experience_assessment={},
                evidence_items=[],
                explanation="Screening failed due to processing error.",
                processing_status=ScreeningResultStatus.FAILED.value,
                error_message=str(e),
            )
            db.add(failed_result)
            await db.flush()

    # 7. Finalize screening run status
    screening_run.processed_applications = processed_count
    screening_run.failed_applications = failed_count
    screening_run.completed_at = utc_now()

    if failed_count == 0:
        screening_run.status = ScreeningRunStatus.COMPLETED.value
    elif processed_count > 0:
        screening_run.status = ScreeningRunStatus.PARTIAL.value
        screening_run.error_summary = "; ".join(error_messages[:5])
    else:
        screening_run.status = ScreeningRunStatus.FAILED.value
        screening_run.error_summary = "; ".join(error_messages[:5])

    await db.commit()
    await db.refresh(screening_run)

    return ScreeningRunResponse.model_validate(screening_run)


async def list_job_screening_runs(
    db: AsyncSession,
    organization_id: uuid.UUID,
    job_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> PaginatedScreeningRunsResponse:
    """List historical screening runs for a specific job."""
    # Verify job belongs to organization
    job_stmt = select(Job.id).where(
        Job.id == job_id,
        Job.organization_id == organization_id,
    )
    job_res = await db.execute(job_stmt)
    if not job_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found in this organization",
        )

    count_stmt = select(func.count(ScreeningRun.id)).where(
        ScreeningRun.job_id == job_id,
        ScreeningRun.organization_id == organization_id,
    )
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    runs_stmt = (
        select(ScreeningRun)
        .where(
            ScreeningRun.job_id == job_id,
            ScreeningRun.organization_id == organization_id,
        )
        .order_by(ScreeningRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    runs_res = await db.execute(runs_stmt)
    runs = runs_res.scalars().all()

    return PaginatedScreeningRunsResponse(
        items=[ScreeningRunResponse.model_validate(r) for r in runs],
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_screening_run_detail(
    db: AsyncSession,
    organization_id: uuid.UUID,
    run_id: uuid.UUID,
) -> ScreeningRunResponse:
    """Fetch details of a single screening run."""
    stmt = select(ScreeningRun).where(
        ScreeningRun.id == run_id,
        ScreeningRun.organization_id == organization_id,
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening run not found in this organization",
        )

    return ScreeningRunResponse.model_validate(run)


async def list_screening_results(
    db: AsyncSession,
    organization_id: uuid.UUID,
    run_id: uuid.UUID,
    status_filter: Optional[str] = None,
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
    limit: int = 50,
    offset: int = 0,
) -> PaginatedScreeningResultsResponse:
    """List ranked screening results for a run with candidate identity details."""
    # Verify run exists for organization
    run_stmt = select(ScreeningRun.id).where(
        ScreeningRun.id == run_id,
        ScreeningRun.organization_id == organization_id,
    )
    run_res = await db.execute(run_stmt)
    if not run_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening run not found in this organization",
        )

    conditions = [
        ScreeningResult.screening_run_id == run_id,
        ScreeningResult.organization_id == organization_id,
    ]

    if status_filter:
        conditions.append(ScreeningResult.processing_status == status_filter.upper())
    if score_min is not None:
        conditions.append(ScreeningResult.total_score >= score_min)
    if score_max is not None:
        conditions.append(ScreeningResult.total_score <= score_max)

    count_stmt = select(func.count(ScreeningResult.id)).where(*conditions)
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    stmt = (
        select(ScreeningResult, Application, CandidateProfile, User, Resume, ScreeningInsight)
        .join(Application, ScreeningResult.application_id == Application.id)
        .join(CandidateProfile, ScreeningResult.candidate_id == CandidateProfile.id)
        .join(User, CandidateProfile.user_id == User.id)
        .join(Resume, ScreeningResult.submitted_resume_id == Resume.id)
        .outerjoin(ScreeningInsight, ScreeningResult.id == ScreeningInsight.screening_result_id)
        .where(*conditions)
        .order_by(ScreeningResult.total_score.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )
    rows = await db.execute(stmt)

    items: List[ScreeningResultListItem] = []
    for s_res, app, cand, user, resume, insight in rows.all():
        snapshot = app.candidate_snapshot or {}
        insight_summary = (insight.insight_data or {}).get("summary") if insight else None
        insight_status = insight.status if insight else None
        items.append(
            ScreeningResultListItem(
                id=s_res.id,
                screening_run_id=s_res.screening_run_id,
                application_id=s_res.application_id,
                candidate_id=s_res.candidate_id,
                candidate_name=snapshot.get("full_name") or user.full_name,
                candidate_email=snapshot.get("email") or user.email,
                candidate_headline=snapshot.get("headline") or cand.headline,
                submitted_resume_id=s_res.submitted_resume_id,
                resume_filename=resume.original_filename,
                total_score=float(s_res.total_score) if s_res.total_score is not None else None,
                required_skill_score=float(s_res.required_skill_score) if s_res.required_skill_score is not None else None,
                preferred_skill_score=float(s_res.preferred_skill_score) if s_res.preferred_skill_score is not None else None,
                experience_score=float(s_res.experience_score) if s_res.experience_score is not None else None,
                matched_skills_count=len(s_res.matched_skills or []),
                missing_evidence_count=len(s_res.missing_evidence or []),
                confidence_level=s_res.confidence_level,
                processing_status=s_res.processing_status,
                insight_summary=insight_summary,
                insight_status=insight_status,
                created_at=s_res.created_at,
            )
        )

    return PaginatedScreeningResultsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_screening_result_detail(
    db: AsyncSession,
    organization_id: uuid.UUID,
    result_id: uuid.UUID,
) -> ScreeningResultDetailResponse:
    """Retrieve full screening result detail including explainability and breakdown."""
    stmt = (
        select(ScreeningResult, Application, CandidateProfile, User, Resume, ScreeningInsight)
        .join(Application, ScreeningResult.application_id == Application.id)
        .join(CandidateProfile, ScreeningResult.candidate_id == CandidateProfile.id)
        .join(User, CandidateProfile.user_id == User.id)
        .join(Resume, ScreeningResult.submitted_resume_id == Resume.id)
        .outerjoin(ScreeningInsight, ScreeningResult.id == ScreeningInsight.screening_result_id)
        .where(
            ScreeningResult.id == result_id,
            ScreeningResult.organization_id == organization_id,
        )
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening result not found in this organization",
        )

    s_res, app, cand, user, resume, insight = row
    snapshot = app.candidate_snapshot or {}
    insight_resp = ScreeningInsightResponse.model_validate(insight) if insight else None

    return ScreeningResultDetailResponse(
        id=s_res.id,
        screening_run_id=s_res.screening_run_id,
        application_id=s_res.application_id,
        candidate_id=s_res.candidate_id,
        candidate_name=snapshot.get("full_name") or user.full_name,
        candidate_email=snapshot.get("email") or user.email,
        candidate_headline=snapshot.get("headline") or cand.headline,
        submitted_resume_id=s_res.submitted_resume_id,
        resume_filename=resume.original_filename,
        total_score=float(s_res.total_score) if s_res.total_score is not None else None,
        required_skill_score=float(s_res.required_skill_score) if s_res.required_skill_score is not None else None,
        preferred_skill_score=float(s_res.preferred_skill_score) if s_res.preferred_skill_score is not None else None,
        experience_score=float(s_res.experience_score) if s_res.experience_score is not None else None,
        matched_skills=s_res.matched_skills or [],
        missing_evidence=s_res.missing_evidence or [],
        preferred_skill_matches=s_res.preferred_skill_matches or [],
        experience_assessment=s_res.experience_assessment or {},
        explanation=s_res.explanation,
        confidence_level=s_res.confidence_level,
        processing_status=s_res.processing_status,
        error_message=s_res.error_message,
        insight=insight_resp,
        created_at=s_res.created_at,
    )


async def retry_candidate_insight(
    db: AsyncSession,
    organization_id: uuid.UUID,
    result_id: uuid.UUID,
) -> ScreeningInsightResponse:
    """Manually retry insight generation for a specific screening result."""
    stmt = (
        select(ScreeningResult, Application, Job, Resume, ScreeningRun)
        .join(Application, ScreeningResult.application_id == Application.id)
        .join(Job, ScreeningResult.job_id == Job.id)
        .join(Resume, ScreeningResult.submitted_resume_id == Resume.id)
        .join(ScreeningRun, ScreeningResult.screening_run_id == ScreeningRun.id)
        .where(
            ScreeningResult.id == result_id,
            ScreeningResult.organization_id == organization_id,
        )
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening result not found in this organization",
        )

    s_res, app, job, resume, run = row
    resume_text = resume.extracted_text or ""
    if not resume_text:
        abs_path = storage_service.get_absolute_path(resume.storage_path)
        if abs_path.exists():
            with open(abs_path, "rb") as f:
                resume_text = pdf_extractor.extract_text(f.read())

    # Build score data from existing result (NEVER altering scores!)
    score_data = {
        "total_score": float(s_res.total_score) if s_res.total_score is not None else 0.0,
        "required_skill_score": float(s_res.required_skill_score) if s_res.required_skill_score is not None else 0.0,
        "preferred_skill_score": float(s_res.preferred_skill_score) if s_res.preferred_skill_score is not None else 0.0,
        "experience_score": float(s_res.experience_score) if s_res.experience_score is not None else 0.0,
        "matched_skills": s_res.matched_skills or [],
        "missing_evidence": s_res.missing_evidence or [],
        "preferred_skill_matches": s_res.preferred_skill_matches or [],
        "experience_assessment": s_res.experience_assessment or {},
        "explanation": s_res.explanation,
    }

    # Generate insight
    insight_schema, model_used, is_fallback = await candidate_insight_generator.generate_insight(
        job_criteria=run.job_snapshot,
        score_data=score_data,
        extracted_projects=[],
        extracted_experience=[],
        resume_text=resume_text,
    )

    # Check if insight already exists
    ins_stmt = select(ScreeningInsight).where(ScreeningInsight.screening_result_id == s_res.id)
    ins_res = await db.execute(ins_stmt)
    insight_rec = ins_res.scalar_one_or_none()

    if insight_rec:
        insight_rec.insight_data = insight_schema.model_dump()
        insight_rec.model_id = model_used
        insight_rec.status = ScreeningInsightStatus.COMPLETED.value
        insight_rec.error_message = None
        insight_rec.updated_at = utc_now()
    else:
        insight_rec = ScreeningInsight(
            screening_result_id=s_res.id,
            screening_run_id=s_res.screening_run_id,
            application_id=s_res.application_id,
            status=ScreeningInsightStatus.COMPLETED.value,
            model_id=model_used,
            prompt_version=INSIGHT_PROMPT_VERSION,
            insight_data=insight_schema.model_dump(),
        )
        db.add(insight_rec)

    await db.commit()
    await db.refresh(insight_rec)
    return ScreeningInsightResponse.model_validate(insight_rec)
