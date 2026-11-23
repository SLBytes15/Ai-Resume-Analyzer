import uuid
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.resume import ResumeListItemResponse, ResumeResponse
from app.services.resume_service import (
    delete_candidate_resume,
    get_candidate_profile_by_user_id,
    get_candidate_resume,
    get_or_create_candidate_profile,
    list_candidate_resumes,
    process_and_create_resume,
    set_active_resume,
)
from app.services.storage_service import storage_service

router = APIRouter()


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a candidate resume PDF",
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """
    Upload a resume PDF.
    Validates PDF format, extracts text with PyMuPDF, and runs local Ollama structured extraction.
    """
    # Ensure candidate profile exists
    candidate = await get_or_create_candidate_profile(db, current_user)

    filename = file.filename or "resume.pdf"
    content = await file.read()

    resume = await process_and_create_resume(
        db=db,
        candidate=candidate,
        file_bytes=content,
        original_filename=filename,
    )

    return ResumeResponse.model_validate(resume)


@router.get(
    "",
    response_model=List[ResumeListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List candidate's uploaded resumes",
)
async def list_resumes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ResumeListItemResponse]:
    """Retrieve all resumes owned by the authenticated candidate."""
    candidate = await get_candidate_profile_by_user_id(db, current_user.id)
    if not candidate:
        return []

    resumes = await list_candidate_resumes(db, candidate.id)
    return [ResumeListItemResponse.model_validate(r) for r in resumes]


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resume details and parsed data",
)
async def get_resume(
    resume_id: uuid.UUID = Path(..., description="Resume UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Retrieve details, extracted text, and AI-parsed data for a specific resume."""
    candidate = await get_candidate_profile_by_user_id(db, current_user.id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    resume = await get_candidate_resume(db, candidate.id, resume_id)
    return ResumeResponse.model_validate(resume)


@router.get(
    "/{resume_id}/download",
    summary="Download original resume PDF file",
)
async def download_resume(
    resume_id: uuid.UUID = Path(..., description="Resume UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Securely download the original uploaded resume PDF."""
    candidate = await get_candidate_profile_by_user_id(db, current_user.id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    resume = await get_candidate_resume(db, candidate.id, resume_id)
    abs_path = storage_service.get_absolute_path(resume.storage_path)

    if not abs_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file does not exist on storage",
        )

    return FileResponse(
        path=str(abs_path),
        media_type=resume.mime_type or "application/pdf",
        filename=resume.original_filename,
    )


@router.patch(
    "/{resume_id}/active",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Set resume as active",
)
async def make_resume_active(
    resume_id: uuid.UUID = Path(..., description="Resume UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Set the specified resume as the candidate's active resume."""
    candidate = await get_candidate_profile_by_user_id(db, current_user.id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    resume = await set_active_resume(db, candidate.id, resume_id)
    return ResumeResponse.model_validate(resume)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete candidate resume",
)
async def delete_resume(
    resume_id: uuid.UUID = Path(..., description="Resume UUID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a resume and remove its stored file."""
    candidate = await get_candidate_profile_by_user_id(db, current_user.id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )

    await delete_candidate_resume(db, candidate.id, resume_id)
    return {"message": "Resume deleted successfully"}
