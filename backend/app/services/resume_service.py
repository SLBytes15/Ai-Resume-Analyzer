import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.application import Application
from app.models.candidate import CandidateProfile, ParsingStatus, Resume
from app.models.user import User
from app.schemas.candidate import CandidateProfileCreate, CandidateProfileUpdate
from app.schemas.resume import ParsedResumeData
from app.services.llm_parser import LLMParserError, llm_parser
from app.services.pdf_extractor import PDFExtractionError, pdf_extractor
from app.services.storage_service import storage_service


# ---------------------------------------------------------------------------
# Candidate Profile Operations
# ---------------------------------------------------------------------------


async def get_candidate_profile_by_user_id(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[CandidateProfile]:
    """Fetch candidate profile for a given user ID."""
    stmt = select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_candidate_profile(
    db: AsyncSession, user: User, profile_in: CandidateProfileCreate
) -> CandidateProfile:
    """Create a new candidate profile for authenticated user."""
    existing = await get_candidate_profile_by_user_id(db, user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate profile already exists for this user",
        )

    profile = CandidateProfile(
        user_id=user.id,
        phone=profile_in.phone,
        location=profile_in.location,
        headline=profile_in.headline,
        professional_summary=profile_in.professional_summary,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def update_candidate_profile(
    db: AsyncSession, profile: CandidateProfile, update_in: CandidateProfileUpdate
) -> CandidateProfile:
    """Update existing candidate profile fields."""
    update_data = update_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(profile, field, val)

    await db.commit()
    await db.refresh(profile)
    return profile


async def get_or_create_candidate_profile(
    db: AsyncSession, user: User
) -> CandidateProfile:
    """Ensure candidate profile exists for user, creating an empty one if not present."""
    profile = await get_candidate_profile_by_user_id(db, user.id)
    if not profile:
        profile = CandidateProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# Resume Operations & Processing Pipeline
# ---------------------------------------------------------------------------


async def list_candidate_resumes(
    db: AsyncSession, candidate_id: uuid.UUID
) -> List[Resume]:
    """List all resumes belonging to a candidate, ordered by newest first."""
    stmt = (
        select(Resume)
        .where(Resume.candidate_id == candidate_id)
        .order_by(Resume.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_candidate_resume(
    db: AsyncSession, candidate_id: uuid.UUID, resume_id: uuid.UUID
) -> Resume:
    """Fetch a specific resume verifying ownership."""
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.candidate_id == candidate_id,
    )
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    return resume


async def process_and_create_resume(
    db: AsyncSession,
    candidate: CandidateProfile,
    file_bytes: bytes,
    original_filename: str,
) -> Resume:
    """
    Execute full resume processing pipeline:
    1. Validation
    2. Secure file persistence
    3. PENDING record creation
    4. Text extraction (PyMuPDF)
    5. AI-powered structured extraction (Ollama)
    6. Record finalization (COMPLETED or FAILED)
    """
    # 1. Validation
    storage_service.validate_pdf_content(file_bytes, original_filename)
    sha256 = storage_service.calculate_sha256(file_bytes)

    # 2. Storage
    resume_id = uuid.uuid4()
    rel_path = await storage_service.save_file_async(candidate.id, resume_id, file_bytes)

    # Check if candidate has any active resume; if not, make this one active
    existing_active = await db.execute(
        select(Resume).where(
            Resume.candidate_id == candidate.id,
            Resume.is_active == True,
        )
    )
    is_first_resume = existing_active.scalar_one_or_none() is None

    # 3. Create initial record
    resume = Resume(
        id=resume_id,
        candidate_id=candidate.id,
        original_filename=original_filename,
        storage_path=rel_path,
        mime_type="application/pdf",
        file_size=len(file_bytes),
        sha256=sha256,
        parsing_status=ParsingStatus.PROCESSING.value,
        is_active=is_first_resume,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    # 4. Extract PDF text
    try:
        extracted_text = await pdf_extractor.extract_text_async(file_bytes)
        resume.extracted_text = extracted_text
        await db.commit()
    except PDFExtractionError as e:
        resume.parsing_status = ParsingStatus.FAILED.value
        resume.parsing_error = str(e)
        await db.commit()
        await db.refresh(resume)
        return resume
    except Exception as e:
        resume.parsing_status = ParsingStatus.FAILED.value
        resume.parsing_error = f"Unexpected PDF extraction error: {str(e)}"
        await db.commit()
        await db.refresh(resume)
        return resume

    # 5. Extract structured data via Ollama
    try:
        parsed_data = await llm_parser.parse_resume(extracted_text)
        resume.parsed_data = parsed_data.model_dump()
        resume.parsing_status = ParsingStatus.COMPLETED.value
        resume.parsing_error = None
    except LLMParserError as e:
        resume.parsing_status = ParsingStatus.FAILED.value
        resume.parsing_error = f"AI extraction error: {str(e)}"
    except Exception as e:
        resume.parsing_status = ParsingStatus.FAILED.value
        resume.parsing_error = f"Unexpected AI parsing error: {str(e)}"

    await db.commit()
    await db.refresh(resume)
    return resume


async def set_active_resume(
    db: AsyncSession, candidate_id: uuid.UUID, resume_id: uuid.UUID
) -> Resume:
    """Set the specified resume as active, deactivating any others atomically."""
    target_resume = await get_candidate_resume(db, candidate_id, resume_id)

    # Deactivate all active resumes for this candidate first
    await db.execute(
        update(Resume)
        .where(
            Resume.candidate_id == candidate_id,
            Resume.is_active == True,
        )
        .values(is_active=False)
    )
    await db.flush()

    # Activate target resume
    target_resume.is_active = True
    await db.commit()
    await db.refresh(target_resume)
    return target_resume


async def delete_candidate_resume(
    db: AsyncSession, candidate_id: uuid.UUID, resume_id: uuid.UUID
) -> None:
    """Delete resume from database and remove stored file."""
    resume = await get_candidate_resume(db, candidate_id, resume_id)

    # Check if resume is pinned to any existing application
    pinned_query = select(func.count(Application.id)).where(
        Application.submitted_resume_id == resume_id
    )
    pinned_res = await db.execute(pinned_query)
    pinned_count = pinned_res.scalar() or 0
    if pinned_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete resume: it is pinned to one or more submitted job applications",
        )

    was_active = resume.is_active
    storage_path = resume.storage_path

    # Delete row
    await db.delete(resume)
    await db.commit()

    # Clean up file on disk
    await storage_service.delete_file_async(storage_path)

    # If deleted resume was active, optionally activate the newest remaining resume
    if was_active:
        remaining = await db.execute(
            select(Resume)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.created_at.desc())
        )
        next_resume = remaining.scalars().first()
        if next_resume:
            next_resume.is_active = True
            await db.commit()
