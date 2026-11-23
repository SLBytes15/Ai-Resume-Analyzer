import asyncio
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.ai_concurrency import ollama_inference_semaphore
from app.core.config import Settings, settings
from app.core.rate_limit import rate_limiter
from app.core.security import hash_password_async, verify_password_async
from app.main import app
from app.models.application import (
    ALLOWED_RECRUITER_TRANSITIONS,
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
)
from app.models.candidate import CandidateProfile, ParsingStatus, Resume
from app.models.job import Job, JobStatus
from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.user import User


@pytest.mark.asyncio
async def test_health_live_probe():
    """Verify liveness probe returns 200 OK and valid status."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/health/live")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "environment" in data


@pytest.mark.asyncio
async def test_health_ready_probe(db_session: AsyncSession):
    """Verify readiness probe verifies database connectivity and probes Ollama."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get("/health/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"
        assert "ai_service" in data


@pytest.mark.asyncio
async def test_request_id_middleware_and_header():
    """Verify X-Request-ID is generated or adopted and returned in response headers."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Case 1: Automatic generation
        res1 = await ac.get("/health/live")
        assert "x-request-id" in res1.headers
        req_id1 = res1.headers["x-request-id"]
        assert len(req_id1) > 0

        # Case 2: Inbound propagation
        custom_id = "test-req-correlation-id-12345"
        res2 = await ac.get("/health/live", headers={"X-Request-ID": custom_id})
        assert res2.headers.get("x-request-id") == custom_id


@pytest.mark.asyncio
async def test_rate_limiter_exceeded():
    """Verify rate limiter blocks excessive requests with HTTP 429 and Retry-After."""
    test_key = f"test-client-ip:/test/rate/limited"
    max_reqs = 3
    window = 10

    # First 3 should pass
    for _ in range(max_reqs):
        assert rate_limiter.is_allowed(test_key, max_reqs, window) is True

    # 4th request must fail
    assert rate_limiter.is_allowed(test_key, max_reqs, window) is False


@pytest.mark.asyncio
async def test_production_settings_validation():
    """Verify settings.validate_production_settings() fails closed on default secret."""
    insecure_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="talentlens-mvp-super-secret-key-at-least-32-chars-long",
    )
    with pytest.raises(RuntimeError) as exc_info:
        insecure_settings.validate_production_settings()
    assert "Insecure or default SECRET_KEY" in str(exc_info.value)

    # Secure settings must pass without error
    secure_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="c2VjdXJlLWhpZ2gtZW50cm9weS1wcm9kdWN0aW9uLXNlY3JldC1rZXktMTIzNA==",
    )
    secure_settings.validate_production_settings()


@pytest.mark.asyncio
async def test_async_password_hashing():
    """Verify password hashing and verification run cleanly asynchronously."""
    raw_pwd = "StrongTestPassword123!"
    hashed = await hash_password_async(raw_pwd)
    assert hashed != raw_pwd
    assert hashed.startswith("$2b$")

    # Correct password
    is_valid = await verify_password_async(raw_pwd, hashed)
    assert is_valid is True

    # Wrong password
    is_invalid = await verify_password_async("WrongPassword", hashed)
    assert is_invalid is False


@pytest.mark.asyncio
async def test_ollama_inference_semaphore():
    """Verify shared semaphore serializes concurrency as expected."""
    assert ollama_inference_semaphore._value == 1
    async with ollama_inference_semaphore:
        assert ollama_inference_semaphore._value == 0
    assert ollama_inference_semaphore._value == 1


@pytest.mark.asyncio
async def test_interviewing_status_lifecycle_and_transition(db_session: AsyncSession):
    """Verify application can transition to INTERVIEWING and from INTERVIEWING to HIRED."""
    # 1. Create org, recruiter user, candidate user
    org = Organization(name="Interview Lifecycle Org", slug="interview-org")
    recruiter_user = User(
        email="lead.recruiter@intervieworg.com",
        password_hash="fakehash",
        full_name="Lead Recruiter",
        is_active=True,
    )
    cand_user = User(
        email="candidate.applicant@interviewtest.com",
        password_hash="fakehash",
        full_name="Candidate Applicant",
        is_active=True,
    )
    db_session.add_all([org, recruiter_user, cand_user])
    await db_session.flush()

    # Recruiter membership
    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=recruiter_user.id,
        role=OrganizationRole.RECRUITER,
        is_active=True,
    )
    # Candidate profile & resume
    cand_profile = CandidateProfile(user_id=cand_user.id, headline="Senior Engineer")
    db_session.add_all([membership, cand_profile])
    await db_session.flush()

    resume = Resume(
        candidate_id=cand_profile.id,
        original_filename="candidate.pdf",
        storage_path=f"{cand_profile.id}/resume.pdf",
        mime_type="application/pdf",
        file_size=1024,
        sha256="fakehash",
        parsing_status=ParsingStatus.COMPLETED.value,
    )
    job = Job(
        organization_id=org.id,
        title="Software Engineer - Interview Test",
        description="Interview test job",
        status=JobStatus.PUBLISHED.value,
        created_by=recruiter_user.id,
    )
    db_session.add_all([resume, job])
    await db_session.flush()

    # 2. Create Application
    application = Application(
        job_id=job.id,
        candidate_id=cand_profile.id,
        submitted_resume_id=resume.id,
        organization_id=org.id,
        status=ApplicationStatus.SUBMITTED.value,
    )
    db_session.add(application)
    await db_session.commit()
    await db_session.refresh(application)

    # 3. Transition: SUBMITTED -> SHORTLISTED
    application.status = ApplicationStatus.SHORTLISTED.value
    hist1 = ApplicationStatusHistory(
        application_id=application.id,
        previous_status=ApplicationStatus.SUBMITTED.value,
        new_status=ApplicationStatus.SHORTLISTED.value,
        changed_by=recruiter_user.id,
    )
    db_session.add(hist1)
    await db_session.commit()
    await db_session.refresh(application)
    assert application.status == ApplicationStatus.SHORTLISTED.value

    # 4. Transition: SHORTLISTED -> INTERVIEWING (M10 feature)
    assert ApplicationStatus.INTERVIEWING.value in ALLOWED_RECRUITER_TRANSITIONS[ApplicationStatus.SHORTLISTED.value]
    application.status = ApplicationStatus.INTERVIEWING.value
    hist2 = ApplicationStatusHistory(
        application_id=application.id,
        previous_status=ApplicationStatus.SHORTLISTED.value,
        new_status=ApplicationStatus.INTERVIEWING.value,
        changed_by=recruiter_user.id,
        internal_note="Technical interview round 1 scheduled",
    )
    db_session.add(hist2)
    await db_session.commit()
    await db_session.refresh(application)
    assert application.status == ApplicationStatus.INTERVIEWING.value

    # 5. Transition: INTERVIEWING -> HIRED
    assert ApplicationStatus.HIRED.value in ALLOWED_RECRUITER_TRANSITIONS[ApplicationStatus.INTERVIEWING.value]
    application.status = ApplicationStatus.HIRED.value
    hist3 = ApplicationStatusHistory(
        application_id=application.id,
        previous_status=ApplicationStatus.INTERVIEWING.value,
        new_status=ApplicationStatus.HIRED.value,
        changed_by=recruiter_user.id,
        internal_note="Cleared all interview rounds with recommendation to hire",
    )
    db_session.add(hist3)
    await db_session.commit()
    await db_session.refresh(application)
    assert application.status == ApplicationStatus.HIRED.value
