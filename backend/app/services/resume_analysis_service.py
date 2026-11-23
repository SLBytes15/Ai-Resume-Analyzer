import logging
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateProfile, Resume
from app.models.resume_analysis import AnalysisStatus, ResumeAnalysis
from app.services.career_guidance_service import (
    CAREER_GUIDANCE_PROMPT_VERSION,
    CAREER_GUIDANCE_SCHEMA_VERSION,
    career_guidance_service,
)
from app.services.deterministic_resume_checker import deterministic_checker

logger = logging.getLogger(__name__)


async def get_candidate_resume_for_analysis(
    db: AsyncSession,
    candidate: CandidateProfile,
    resume_id: uuid.UUID,
) -> Resume:
    """Fetch resume and ensure it belongs to the authenticated candidate."""
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.candidate_id == candidate.id,
    )
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    return resume


async def create_resume_analysis(
    db: AsyncSession,
    candidate: CandidateProfile,
    resume_id: uuid.UUID,
    target_role: Optional[str] = None,
) -> ResumeAnalysis:
    """
    Create and execute an advisory resume analysis for the authenticated candidate.
    Enforces resume ownership, usable extracted text validation, and prevents duplicate in-flight requests.
    """
    resume = await get_candidate_resume_for_analysis(db, candidate, resume_id)

    # Validate usable text
    text = (resume.extracted_text or "").strip()
    if not text or len(text.split()) < 15:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Resume does not contain sufficient extracted text for analysis. Ensure a text-based PDF is uploaded.",
        )

    # Concurrency prevention: prevent duplicate PENDING or PROCESSING analysis for identical resume and target role
    stmt = select(ResumeAnalysis).where(
        ResumeAnalysis.resume_id == resume.id,
        ResumeAnalysis.candidate_id == candidate.id,
        ResumeAnalysis.target_role == target_role,
        ResumeAnalysis.status.in_([AnalysisStatus.PENDING.value, AnalysisStatus.PROCESSING.value]),
    )
    in_flight = (await db.execute(stmt)).scalar_one_or_none()
    if in_flight:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An analysis for this resume version and target role is currently in progress",
        )

    # 1. Initialize record
    analysis = ResumeAnalysis(
        candidate_id=candidate.id,
        resume_id=resume.id,
        resume_sha256=resume.sha256,
        target_role=target_role,
        status=AnalysisStatus.PROCESSING.value,
        prompt_version=CAREER_GUIDANCE_PROMPT_VERSION,
        schema_version=CAREER_GUIDANCE_SCHEMA_VERSION,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # 2. Run deterministic checks
    checks = deterministic_checker.analyze(resume.extracted_text, resume.parsed_data)
    analysis.deterministic_checks = checks.model_dump()

    # 3. Run LLM career guidance
    try:
        payload, model_used, is_fallback, error_msg = await career_guidance_service.generate_career_guidance(
            resume_text=resume.extracted_text,
            parsed_data=resume.parsed_data or {},
            deterministic_checks=checks,
            target_role=target_role,
        )
        analysis.analysis_data = payload.model_dump()
        analysis.model_name = model_used
        if is_fallback:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = error_msg
        else:
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.error_message = None
    except Exception as exc:
        logger.error(f"Error executing career guidance for analysis {analysis.id}: {exc}")
        analysis.status = AnalysisStatus.FAILED.value
        analysis.error_message = f"Analysis execution failed: {str(exc)}"
        # Generate safe fallback payload so candidate has guidance
        fallback = career_guidance_service.generate_deterministic_fallback(
            resume_text=resume.extracted_text,
            parsed_data=resume.parsed_data or {},
            deterministic_checks=checks,
            target_role=target_role,
        )
        analysis.analysis_data = fallback.model_dump()

    await db.commit()
    await db.refresh(analysis)
    return analysis


async def list_resume_analyses(
    db: AsyncSession,
    candidate: CandidateProfile,
    resume_id: uuid.UUID,
) -> List[ResumeAnalysis]:
    """List all historical analyses for a specific candidate resume."""
    # Ensure candidate owns resume
    await get_candidate_resume_for_analysis(db, candidate, resume_id)

    stmt = (
        select(ResumeAnalysis)
        .where(
            ResumeAnalysis.resume_id == resume_id,
            ResumeAnalysis.candidate_id == candidate.id,
        )
        .order_by(ResumeAnalysis.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_resume_analysis_by_id(
    db: AsyncSession,
    candidate: CandidateProfile,
    analysis_id: uuid.UUID,
) -> ResumeAnalysis:
    """Fetch an analysis by ID, strictly enforcing candidate ownership."""
    stmt = select(ResumeAnalysis).where(
        ResumeAnalysis.id == analysis_id,
        ResumeAnalysis.candidate_id == candidate.id,
    )
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume analysis not found",
        )
    return analysis


async def retry_resume_analysis(
    db: AsyncSession,
    candidate: CandidateProfile,
    analysis_id: uuid.UUID,
) -> ResumeAnalysis:
    """Retry an eligible failed resume analysis."""
    analysis = await get_resume_analysis_by_id(db, candidate, analysis_id)

    if analysis.status != AnalysisStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed analyses can be retried",
        )

    resume = await get_candidate_resume_for_analysis(db, candidate, analysis.resume_id)

    analysis.status = AnalysisStatus.PROCESSING.value
    await db.commit()
    await db.refresh(analysis)

    # Re-run deterministic checks
    checks = deterministic_checker.analyze(resume.extracted_text, resume.parsed_data)
    analysis.deterministic_checks = checks.model_dump()

    try:
        payload, model_used, is_fallback, error_msg = await career_guidance_service.generate_career_guidance(
            resume_text=resume.extracted_text or "",
            parsed_data=resume.parsed_data or {},
            deterministic_checks=checks,
            target_role=analysis.target_role,
        )
        analysis.analysis_data = payload.model_dump()
        analysis.model_name = model_used
        if is_fallback:
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = error_msg
        else:
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.error_message = None
    except Exception as exc:
        logger.error(f"Retry failed for analysis {analysis.id}: {exc}")
        analysis.status = AnalysisStatus.FAILED.value
        analysis.error_message = f"Retry failed: {str(exc)}"

    await db.commit()
    await db.refresh(analysis)
    return analysis
