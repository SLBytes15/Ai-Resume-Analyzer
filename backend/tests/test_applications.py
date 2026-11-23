import io
import uuid
from unittest.mock import AsyncMock, patch
import fitz
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.application import Application, ApplicationStatus, ApplicationStatusHistory
from app.models.job import JobStatus
from app.models.organization import OrganizationRole
from app.schemas.resume import ParsedResumeData


def make_pdf(text: str = "Candidate Resume\nSkills: Python, FastAPI, PostgreSQL") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def make_scanned_pdf() -> bytes:
    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def mock_ollama():
    mock_data = ParsedResumeData(
        full_name="Alice Candidate",
        email="alice@example.com",
        phone="+1-555-0199",
        professional_summary="Backend Engineer",
        skills=["Python", "FastAPI", "SQL"],
        education=[],
        experience=[],
        projects=[],
        certifications=[],
    )
    with patch("app.services.resume_service.llm_parser.parse_resume", new_callable=AsyncMock) as m:
        m.return_value = mock_data
        yield m


async def register_user(client: AsyncClient, email: str, name: str) -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "full_name": name},
    )
    assert res.status_code == 201
    return res.json()["access_token"]


async def create_org(client: AsyncClient, token: str, name: str, slug: str) -> str:
    res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": name, "slug": slug},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    return res.json()["id"]


async def create_job(client: AsyncClient, token: str, org_id: str, title: str = "Backend Engineer") -> str:
    res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={
            "title": title,
            "description": "Looking for backend engineer",
            "workplace_type": "REMOTE",
            "employment_type": "FULL_TIME",
            "required_skills": ["Python", "FastAPI"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    return res.json()["id"]


async def publish_job(client: AsyncClient, token: str, org_id: str, job_id: str):
    res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200


async def create_candidate_with_resume(client: AsyncClient, email: str, name: str, resume_text: str = "Alice Resume") -> tuple[str, str]:
    token = await register_user(client, email, name)
    # Create profile
    res_prof = await client.post(
        "/api/v1/candidates/me/profile",
        json={"phone": "+1234567890", "location": "Bengaluru", "headline": "Software Engineer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_prof.status_code == 201

    # Upload resume
    pdf_bytes = make_pdf(resume_text)
    files = {"file": ("alice_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_upload = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_upload.status_code == 201
    resume_id = res_upload.json()["id"]
    return token, resume_id


# ===========================================================================
# 1. Submission Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_candidate_applies_successfully_to_published_job(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand_token, resume_id = await create_candidate_with_resume(client, "alice@candidate.com", "Alice Smith")

    # Apply
    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume_id, "cover_letter": "I love building APIs with FastAPI."},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert apply_res.status_code == 201
    data = apply_res.json()
    assert data["job_id"] == job_id
    assert data["organization_id"] == org_id
    assert data["organization_name"] == "Acme Corp"
    assert data["submitted_resume_id"] == resume_id
    assert data["resume_filename"] == "alice_resume.pdf"
    assert data["status"] == "SUBMITTED"
    assert data["cover_letter"] == "I love building APIs with FastAPI."
    assert data["withdrawn_at"] is None


@pytest.mark.asyncio
async def test_candidate_cannot_apply_to_draft_or_closed_job(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Draft Job")

    cand_token, resume_id = await create_candidate_with_resume(client, "alice@candidate.com", "Alice Smith")

    # 1. Draft job rejected
    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert apply_res.status_code == 400
    assert "not open for applications" in apply_res.json()["detail"].lower()

    # 2. Publish then close job
    await publish_job(client, recruiter_token, org_id, job_id)
    close_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/close",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert close_res.status_code == 200

    # 3. Closed job rejected
    apply_res2 = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert apply_res2.status_code == 400
    assert "not open for applications" in apply_res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_candidate_cannot_apply_using_another_candidates_resume(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand1_token, resume1_id = await create_candidate_with_resume(client, "alice@candidate.com", "Alice Smith")
    cand2_token, _ = await create_candidate_with_resume(client, "bob@candidate.com", "Bob Jones")

    # Candidate 2 tries to use Candidate 1's resume
    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume1_id},
        headers={"Authorization": f"Bearer {cand2_token}"},
    )
    assert apply_res.status_code == 404
    assert "resume not found" in apply_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_duplicate_applications_rejected_with_409(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand_token, resume_id = await create_candidate_with_resume(client, "alice@candidate.com", "Alice Smith")

    # First apply
    apply1 = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert apply1.status_code == 201

    # Second apply (duplicate)
    apply2 = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert apply2.status_code == 409
    assert "already submitted an application" in apply2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_missing_candidate_profile_handled(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    # User with no profile
    user_token = await register_user(client, "noprofile@candidate.com", "No Profile")
    fake_resume_id = str(uuid.uuid4())

    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": fake_resume_id},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert apply_res.status_code == 404
    assert "candidate profile not found" in apply_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_scanned_failed_resume_rejected_for_application(client: AsyncClient):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand_token = await register_user(client, "scanned@candidate.com", "Scanned User")
    await client.post(
        "/api/v1/candidates/me/profile",
        json={"phone": "+1234567890", "location": "Bengaluru"},
        headers={"Authorization": f"Bearer {cand_token}"},
    )

    # Upload empty scanned pdf (which causes FAILED parsing_status)
    blank_pdf = make_scanned_pdf()
    files = {"file": ("blank.pdf", io.BytesIO(blank_pdf), "application/pdf")}
    res_upload = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert res_upload.status_code == 201
    assert res_upload.json()["parsing_status"] == "FAILED"
    failed_resume_id = res_upload.json()["id"]

    # Try applying with failed resume
    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": failed_resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert apply_res.status_code == 422
    assert "failed parsing" in apply_res.json()["detail"].lower()


# ===========================================================================
# 2. Resume Version Pinning and Immutability Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_resume_pinning_and_deletion_protection(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand_token, resume1_id = await create_candidate_with_resume(client, "alice@candidate.com", "Alice Smith", "Resume V1 Content")

    # Apply with Resume V1
    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume1_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert apply_res.status_code == 201
    app_id = apply_res.json()["id"]
    assert apply_res.json()["submitted_resume_id"] == resume1_id

    # 1. Candidate uploads a newer Resume V2
    pdf_v2 = make_pdf("Resume V2 Updated Content")
    files_v2 = {"file": ("alice_resume_v2.pdf", io.BytesIO(pdf_v2), "application/pdf")}
    upload_v2 = await client.post(
        "/api/v1/resumes/upload",
        files=files_v2,
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert upload_v2.status_code == 201
    resume2_id = upload_v2.json()["id"]

    # Verify candidate can activate Resume V2
    act_res = await client.patch(
        f"/api/v1/resumes/{resume2_id}/active",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert act_res.status_code == 200

    # 2. Existing application MUST still be pinned to Resume V1
    app_check = await client.get(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert app_check.status_code == 200
    assert app_check.json()["submitted_resume_id"] == resume1_id
    assert app_check.json()["resume_filename"] == "alice_resume.pdf"

    # 3. Candidate CANNOT delete pinned Resume V1
    del_res = await client.delete(
        f"/api/v1/resumes/{resume1_id}",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert del_res.status_code == 409
    assert "pinned to one or more submitted job applications" in del_res.json()["detail"].lower()

    # 4. Candidate CAN delete unpinned Resume V2
    del_v2 = await client.delete(
        f"/api/v1/resumes/{resume2_id}",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert del_v2.status_code == 200

    # 5. Recruiter downloads the exact submitted Resume V1 file
    recruiter_download = await client.get(
        f"/api/v1/organizations/{org_id}/applications/{app_id}/resume",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert recruiter_download.status_code == 200
    assert recruiter_download.headers["content-type"] == "application/pdf"
    assert "alice_resume.pdf" in recruiter_download.headers.get("content-disposition", "")
    assert len(recruiter_download.content) > 0


# ===========================================================================
# 3. Candidate Access and Withdrawal Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_candidate_list_and_detail_isolation(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand1_token, resume1_id = await create_candidate_with_resume(client, "cand1@test.com", "Cand One")
    cand2_token, resume2_id = await create_candidate_with_resume(client, "cand2@test.com", "Cand Two")

    # Cand 1 applies
    apply1 = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume1_id},
        headers={"Authorization": f"Bearer {cand1_token}"},
    )
    app1_id = apply1.json()["id"]

    # Cand 2 lists applications -> should be empty
    list_cand2 = await client.get(
        "/api/v1/applications/me",
        headers={"Authorization": f"Bearer {cand2_token}"},
    )
    assert list_cand2.status_code == 200
    assert list_cand2.json()["total"] == 0
    assert len(list_cand2.json()["items"]) == 0

    # Cand 2 tries to view Cand 1 application -> 404
    detail_cand2 = await client.get(
        f"/api/v1/applications/{app1_id}",
        headers={"Authorization": f"Bearer {cand2_token}"},
    )
    assert detail_cand2.status_code == 404

    # Cand 1 views own application -> 200
    detail_cand1 = await client.get(
        f"/api/v1/applications/{app1_id}",
        headers={"Authorization": f"Bearer {cand1_token}"},
    )
    assert detail_cand1.status_code == 200
    assert detail_cand1.json()["id"] == app1_id


@pytest.mark.asyncio
async def test_candidate_withdraw_application(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand_token, resume_id = await create_candidate_with_resume(client, "cand@test.com", "Candidate")
    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    app_id = apply_res.json()["id"]

    # Withdraw application
    withdraw_res = await client.post(
        f"/api/v1/applications/{app_id}/withdraw",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert withdraw_res.status_code == 200
    assert withdraw_res.json()["status"] == "WITHDRAWN"
    assert withdraw_res.json()["withdrawn_at"] is not None

    # Cannot withdraw again
    withdraw_again = await client.post(
        f"/api/v1/applications/{app_id}/withdraw",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert withdraw_again.status_code == 400


# ===========================================================================
# 4. Recruiter Access and Status Lifecycle Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_recruiter_status_lifecycle_and_notes(client: AsyncClient, mock_ollama):
    recruiter_token = await register_user(client, "recruiter@corp.com", "Recruiter Bob")
    org_id = await create_org(client, recruiter_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, recruiter_token, org_id, "Python Dev")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand_token, resume_id = await create_candidate_with_resume(client, "cand@test.com", "Alice Smith")
    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    app_id = apply_res.json()["id"]

    # 1. Recruiter moves SUBMITTED -> UNDER_REVIEW with internal note
    patch1 = await client.patch(
        f"/api/v1/organizations/{org_id}/applications/{app_id}/status",
        json={"status": "UNDER_REVIEW", "internal_note": "Reviewed GitHub profile, looks strong."},
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert patch1.status_code == 200
    assert patch1.json()["status"] == "UNDER_REVIEW"
    history = patch1.json()["status_history"]
    assert len(history) == 2
    assert history[-1]["new_status"] == "UNDER_REVIEW"
    assert history[-1]["internal_note"] == "Reviewed GitHub profile, looks strong."

    # 2. Recruiter moves UNDER_REVIEW -> SHORTLISTED
    patch2 = await client.patch(
        f"/api/v1/organizations/{org_id}/applications/{app_id}/status",
        json={"status": "SHORTLISTED", "internal_note": "Passed technical phone screen."},
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert patch2.status_code == 200
    assert patch2.json()["status"] == "SHORTLISTED"

    # 3. Recruiter moves SHORTLISTED -> HIRED
    patch3 = await client.patch(
        f"/api/v1/organizations/{org_id}/applications/{app_id}/status",
        json={"status": "HIRED", "internal_note": "Offer accepted!"},
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert patch3.status_code == 200
    assert patch3.json()["status"] == "HIRED"

    # 4. From HIRED, invalid transition should be rejected
    invalid_patch = await client.patch(
        f"/api/v1/organizations/{org_id}/applications/{app_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert invalid_patch.status_code == 400
    assert "invalid status transition" in invalid_patch.json()["detail"].lower()

    # 5. Recruiter CANNOT mark an application as WITHDRAWN
    withdrawn_patch = await client.patch(
        f"/api/v1/organizations/{org_id}/applications/{app_id}/status",
        json={"status": "WITHDRAWN"},
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert withdrawn_patch.status_code == 400
    assert "cannot mark an application as withdrawn" in withdrawn_patch.json()["detail"].lower()

    # 6. Candidate endpoint does NOT expose internal notes or status history
    cand_detail = await client.get(
        f"/api/v1/applications/{app_id}",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert cand_detail.status_code == 200
    assert "internal_note" not in cand_detail.json()
    assert "status_history" not in cand_detail.json()


@pytest.mark.asyncio
async def test_viewer_role_cannot_update_application_status(client: AsyncClient, mock_ollama):
    owner_token = await register_user(client, "owner@corp.com", "Owner")
    org_id = await create_org(client, owner_token, "Acme Corp", "acme-corp")
    job_id = await create_job(client, owner_token, org_id, "Python Dev")
    await publish_job(client, owner_token, org_id, job_id)

    # Add viewer member
    viewer_token = await register_user(client, "viewer@corp.com", "Viewer")
    add_member = await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "viewer@corp.com", "role": "VIEWER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert add_member.status_code == 201

    cand_token, resume_id = await create_candidate_with_resume(client, "cand@test.com", "Cand")
    apply_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    app_id = apply_res.json()["id"]

    # Viewer can read applications
    viewer_list = await client.get(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/applications",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_list.status_code == 200
    assert viewer_list.json()["total"] == 1

    # Viewer cannot update status
    viewer_patch = await client.patch(
        f"/api/v1/organizations/{org_id}/applications/{app_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_patch.status_code == 403


# ===========================================================================
# 5. Cross-Tenant and Privacy Isolation Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_cross_organization_and_resume_isolation(client: AsyncClient, mock_ollama):
    # Setup Org A and Job A
    token_a = await register_user(client, "recruiter_a@org-a.com", "Recruiter A")
    org_a = await create_org(client, token_a, "Org A", "org-a")
    job_a = await create_job(client, token_a, org_a, "Job A")
    await publish_job(client, token_a, org_a, job_a)

    # Setup Org B and Job B
    token_b = await register_user(client, "recruiter_b@org-b.com", "Recruiter B")
    org_b = await create_org(client, token_b, "Org B", "org-b")
    job_b = await create_job(client, token_b, org_b, "Job B")
    await publish_job(client, token_b, org_b, job_b)

    # Candidate applies to Org A's job
    cand_token, resume_id = await create_candidate_with_resume(client, "cand@test.com", "Applicant")
    apply_a = await client.post(
        f"/api/v1/jobs/{job_a}/applications",
        json={"resume_id": resume_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    app_a_id = apply_a.json()["id"]

    # 1. Org B recruiter cannot see Org A's applications in general list
    list_b = await client.get(
        f"/api/v1/organizations/{org_b}/applications",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0

    # 2. Org B recruiter cannot get details of Org A's application
    detail_b = await client.get(
        f"/api/v1/organizations/{org_b}/applications/{app_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert detail_b.status_code == 404

    # 3. Org B recruiter cannot download resume through Org B endpoint
    resume_b = await client.get(
        f"/api/v1/organizations/{org_b}/applications/{app_a_id}/resume",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resume_b.status_code == 404

    # 4. Org B recruiter cannot access Org A endpoint (403 forbidden)
    resume_b_cross = await client.get(
        f"/api/v1/organizations/{org_a}/applications/{app_a_id}/resume",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resume_b_cross.status_code == 403

    # 5. Org B recruiter cannot update status of Org A's application
    patch_b = await client.patch(
        f"/api/v1/organizations/{org_a}/applications/{app_a_id}/status",
        json={"status": "UNDER_REVIEW"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert patch_b.status_code == 403


@pytest.mark.asyncio
async def test_database_constraints_direct(db_session: AsyncSession):
    """Verify unique constraint and status check constraints at database level."""
    from app.models.organization import Organization
    from app.models.job import Job
    from app.models.candidate import CandidateProfile, Resume
    from app.models.user import User
    from app.models.application import Application
    from sqlalchemy.exc import IntegrityError

    # Create dummy records
    user = User(email="db_test@example.com", password_hash="hash", full_name="DB Test User")
    db_session.add(user)
    await db_session.flush()

    org = Organization(name="DB Test Org", slug="db-test-org")
    db_session.add(org)
    await db_session.flush()

    job = Job(
        organization_id=org.id,
        created_by=user.id,
        title="DB Test Job",
        description="DB Test Desc",
        workplace_type="REMOTE",
        employment_type="FULL_TIME",
        required_skills=["Python"],
    )
    db_session.add(job)

    cand = CandidateProfile(user_id=user.id)
    db_session.add(cand)
    await db_session.flush()

    resume = Resume(
        candidate_id=cand.id,
        original_filename="db_resume.pdf",
        storage_path="db/test.pdf",
        file_size=1024,
        sha256="db_hash",
        parsing_status="COMPLETED",
    )
    db_session.add(resume)
    await db_session.flush()

    app1 = Application(
        job_id=job.id,
        candidate_id=cand.id,
        submitted_resume_id=resume.id,
        organization_id=org.id,
        status="SUBMITTED",
    )
    db_session.add(app1)
    await db_session.flush()

    # 1. Duplicate application violates unique constraint
    app_duplicate = Application(
        job_id=job.id,
        candidate_id=cand.id,
        submitted_resume_id=resume.id,
        organization_id=org.id,
        status="SUBMITTED",
    )
    db_session.add(app_duplicate)
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()

    # 2. Deleting pinned resume violates foreign key constraint (RESTRICT)
    db_session.add(user)
    db_session.add(org)
    db_session.add(job)
    db_session.add(cand)
    db_session.add(resume)
    db_session.add(app1)
    await db_session.flush()

    await db_session.delete(resume)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()

