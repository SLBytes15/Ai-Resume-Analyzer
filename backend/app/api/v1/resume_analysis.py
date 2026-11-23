import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.resume_analysis import (
    ResumeAnalysisCreateRequest,
    ResumeAnalysisListItem,
    ResumeAnalysisResponse,
)
from app.services.resume_analysis_service import (
    create_resume_analysis,
    get_resume_analysis_by_id,
    list_resume_analyses,
    retry_resume_analysis,
)
from app.services.resume_service import get_or_create_candidate_profile

router = APIRouter()


@router.post(
    "/resumes/{resume_id}/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request advisory Resume Intelligence & Career Guidance analysis",
)
async def analyze_candidate_resume(
    resume_id: uuid.UUID = Path(..., description="Resume UUID"),
    payload: ResumeAnalysisCreateRequest = ResumeAnalysisCreateRequest(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeAnalysisResponse:
    """
    Generate an evidence-grounded resume analysis and career guidance report.
    Combines deterministic text quality checks with LLM qualitative feedback.
    """
    candidate = await get_or_create_candidate_profile(db, current_user)
    analysis = await create_resume_analysis(
        db=db,
        candidate=candidate,
        resume_id=resume_id,
        target_role=payload.target_role,
    )
    return ResumeAnalysisResponse.model_validate(analysis)


@router.get(
    "/resumes/{resume_id}/analyses",
    response_model=List[ResumeAnalysisListItem],
    status_code=status.HTTP_200_OK,
    summary="List historical analyses for a specific resume",
)
async def get_analyses_for_resume(
    resume_id: uuid.UUID = Path(..., description="Resume UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ResumeAnalysisListItem]:
    """Retrieve historical career guidance analyses associated with a specific resume version."""
    candidate = await get_or_create_candidate_profile(db, current_user)
    analyses = await list_resume_analyses(
        db=db,
        candidate=candidate,
        resume_id=resume_id,
    )

    items = []
    for a in analyses:
        summary_text = None
        if a.analysis_data and isinstance(a.analysis_data, dict):
            summary_text = a.analysis_data.get("overall_summary")
        items.append(
            ResumeAnalysisListItem(
                id=a.id,
                resume_id=a.resume_id,
                target_role=a.target_role,
                status=a.status,
                overall_summary=summary_text,
                created_at=a.created_at,
            )
        )
    return items


@router.get(
    "/analyses/{analysis_id}",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full details of a specific resume analysis",
)
async def get_analysis_detail(
    analysis_id: uuid.UUID = Path(..., description="Analysis UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeAnalysisResponse:
    """Retrieve complete breakdown for a candidate's resume analysis."""
    candidate = await get_or_create_candidate_profile(db, current_user)
    analysis = await get_resume_analysis_by_id(
        db=db,
        candidate=candidate,
        analysis_id=analysis_id,
    )
    return ResumeAnalysisResponse.model_validate(analysis)


@router.post(
    "/analyses/{analysis_id}/retry",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Retry a failed resume analysis",
)
async def retry_failed_analysis(
    analysis_id: uuid.UUID = Path(..., description="Analysis UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeAnalysisResponse:
    """Retry execution for an analysis that previously failed."""
    candidate = await get_or_create_candidate_profile(db, current_user)
    analysis = await retry_resume_analysis(
        db=db,
        candidate=candidate,
        analysis_id=analysis_id,
    )
    return ResumeAnalysisResponse.model_validate(analysis)
