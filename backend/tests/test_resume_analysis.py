import io
import uuid
from unittest.mock import AsyncMock, patch
import fitz
import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import CandidateProfile, ParsingStatus, Resume
from app.models.organization import OrganizationRole
from app.models.resume_analysis import AnalysisStatus, ResumeAnalysis
from app.schemas.resume import ParsedResumeData
from app.schemas.resume_analysis import (
    DeterministicChecksData,
    ImprovementPriorityLevel,
    LLMAnalysisPayload,
    ResumeAnalysisResponse,
)
from app.services.career_guidance_service import career_guidance_service
from app.services.deterministic_resume_checker import deterministic_checker


def make_pdf(text: str = "Jane Doe\nEmail: jane@example.com\nPhone: 555-123-4567\n\nSkills: Python, FastAPI, Docker, SQL\n\nExperience:\nBackend Engineer at Acme Corp (2021 - 2024)\nDeveloped high-performance REST APIs reducing latency by 35% across 50k users.\n\nProjects:\nMicroservices Gateway: Built using FastAPI and Redis to handle 2000 rps.\n\nEducation:\nBS Computer Science (2017 - 2021)") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def mock_ollama_parser():
    mock_data = ParsedResumeData(
        full_name="Jane Doe",
        email="jane@example.com",
        phone="555-123-4567",
        professional_summary="Backend Engineer with experience in Python and FastAPI",
        skills=["Python", "FastAPI", "Docker", "SQL"],
        education=[{"institution": "Tech University", "degree": "BS Computer Science", "start_date": "2017", "end_date": "2021"}],
        experience=[{"company": "Acme Corp", "job_title": "Backend Engineer", "start_date": "2021", "end_date": "2024", "description": "Developed REST APIs reducing latency by 35%"}],
        projects=[{"name": "Microservices Gateway", "technologies": ["FastAPI", "Redis"], "description": "Built gateway handling 2000 rps"}],
        certifications=[],
    )
    with patch("app.services.resume_service.llm_parser.parse_resume", new_callable=AsyncMock) as m:
        m.return_value = mock_data
        yield m


@pytest.fixture
def mock_career_guidance_llm():
    mock_llm_json = """{
      "overall_summary": "Strong backend candidate with practical API engineering experience and evidenced performance metrics.",
      "strengths": [
        {
          "title": "Demonstrated API Engineering",
          "description": "Extensive practical development using FastAPI and Python.",
          "supporting_evidence": ["Developed high-performance REST APIs", "Microservices Gateway"]
        }
      ],
      "skills_analysis": {
        "demonstrated_skills": ["Python", "FastAPI"],
        "skills_with_limited_evidence": ["Docker", "SQL"]
      },
      "project_analysis": [
        {
          "project_name": "Microservices Gateway",
          "what_is_demonstrated": "High throughput routing with FastAPI and Redis",
          "what_is_missing": "Architectural resilience and failover mechanisms",
          "suggested_improvement": "Detail caching strategy and load testing benchmarks"
        }
      ],
      "experience_analysis": [
        {
          "role_or_experience": "Backend Engineer at Acme Corp",
          "demonstrated_contributions": "API development with 35% latency reduction",
          "improvement_suggestions": "Quantify server cost savings resulting from the optimization"
        }
      ],
      "missing_information": [
        "Testing methodologies (e.g. pytest, unit test coverage) are not mentioned"
      ],
      "improvement_priorities": [
        {
          "priority": "HIGH",
          "issue": "Elaborate on Docker and SQL usage",
          "why_it_matters": "Skills listed without context appear as unverified keywords",
          "suggested_action": "Add bullet points detailing database schemas and containerization workflows"
        }
      ],
      "target_role_alignment": {
        "target_role": "Backend Developer",
        "alignment_summary": "High alignment with backend engineering requirements.",
        "relevant_strengths": ["FastAPI", "Python", "API latency reduction"],
        "missing_relevant_evidence": ["Distributed system caching"]
      },
      "limitations_and_uncertainties": [
        "Analysis based on extracted text only without visual layout assessment"
      ]
    }"""
    with patch.object(career_guidance_service, "_query_ollama", new_callable=AsyncMock) as m:
        m.return_value = mock_llm_json
        yield m


async def register_user(client: AsyncClient, email: str, name: str) -> str:
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "full_name": name},
    )
    assert res.status_code == 201
    return res.json()["access_token"]


async def upload_resume(client: AsyncClient, token: str, pdf_bytes: bytes, filename: str = "test_resume.pdf") -> str:
    res = await client.post(
        "/api/v1/resumes/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert res.status_code == 201
    return res.json()["id"]


# ---------------------------------------------------------------------------
# Unit Tests: Deterministic Resume Checks
# ---------------------------------------------------------------------------


def test_deterministic_resume_checker_full_features():
    """Verify deterministic static text checks identifying sections, metrics, contact info, and dates."""
    resume_text = (
        "Jane Doe\njane@example.com\n555-123-4567\ngithub.com/janedoe\n\n"
        "Professional Summary\nExperienced software engineer with 5 years in backend development.\n\n"
        "Technical Skills\nPython, FastAPI, Docker, PostgreSQL\n\n"
        "Work Experience\nSenior Backend Engineer at Acme Corp (2020 - 2024)\n"
        "Reduced query latency by 45% and improved API throughput across 100k users.\n\n"
        "Projects\nData Pipeline: Built scalable ingestion pipeline processing 5000 rps.\n\n"
        "Education\nBS Computer Science (2016 - 2020)"
    )

    parsed_data = {
        "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
        "experience": [{"company": "Acme Corp", "job_title": "Senior Backend Engineer", "start_date": "2020", "end_date": "2024", "description": "Reduced latency"}],
        "projects": [{"name": "Data Pipeline", "description": "Built scalable ingestion pipeline processing 5000 rps"}],
        "education": [{"institution": "State University", "start_date": "2016", "end_date": "2020"}],
    }

    checks = deterministic_checker.analyze(resume_text, parsed_data)

    assert isinstance(checks, DeterministicChecksData)
    assert checks.word_count > 40
    assert checks.contact_info["has_email"] is True
    assert checks.contact_info["has_phone"] is True
    assert checks.contact_info["has_github"] is True
    assert "skills" in checks.sections_detected
    assert "experience" in checks.sections_detected
    assert "projects" in checks.sections_detected
    assert "education" in checks.sections_detected
    assert checks.measurable_outcomes["has_metrics"] is True
    assert checks.measurable_outcomes["metrics_count"] >= 1
    assert "layout_notice" in checks.model_dump()


def test_deterministic_resume_checker_detects_missing_elements():
    """Verify missing sections, missing contact info, and missing metrics produce appropriate advisory findings."""
    resume_text = "Just some text without any sections or contact information."
    checks = deterministic_checker.analyze(resume_text, {})

    assert checks.contact_info["has_email"] is False
    assert "skills" in checks.missing_sections
    assert "experience" in checks.missing_sections
    assert checks.measurable_outcomes["has_metrics"] is False
    assert any(f.category == "CONTACT_INFO" and f.level == "WARNING" for f in checks.findings)
    assert any(f.category == "SECTIONS" and f.level == "WARNING" for f in checks.findings)
    assert any(f.category == "METRICS" and f.level == "ADVISORY" for f in checks.findings)


# ---------------------------------------------------------------------------
# Unit Tests: Fallback Generator & LLM Handling
# ---------------------------------------------------------------------------


def test_career_guidance_deterministic_fallback():
    """Verify non-LLM fallback produces valid, evidence-grounded career guidance payload."""
    resume_text = "Developer resume with Python, Django, PostgreSQL. Built CRM App. 3 years experience at Beta Labs."
    parsed_data = {
        "skills": ["Python", "Django", "PostgreSQL"],
        "experience": [{"company": "Beta Labs", "job_title": "Developer", "description": "Built features"}],
        "projects": [{"name": "CRM App", "description": "Web app in Django", "technologies": ["Python", "Django"]}],
    }
    checks = deterministic_checker.analyze(resume_text, parsed_data)

    fallback = career_guidance_service.generate_deterministic_fallback(
        resume_text=resume_text,
        parsed_data=parsed_data,
        deterministic_checks=checks,
        target_role="Full Stack Developer",
    )

    assert isinstance(fallback, LLMAnalysisPayload)
    assert "CRM App" in fallback.project_analysis[0].project_name
    assert len(fallback.strengths) >= 1
    assert fallback.target_role_alignment is not None
    assert fallback.target_role_alignment.target_role == "Full Stack Developer"
    assert len(fallback.improvement_priorities) >= 1
    assert any(p.priority == ImprovementPriorityLevel.HIGH for p in fallback.improvement_priorities)


@pytest.mark.asyncio
async def test_career_guidance_malformed_json_triggers_fallback():
    """Verify that if Ollama returns malformed or non-JSON output, fallback is triggered."""
    with patch.object(career_guidance_service, "_query_ollama", new_callable=AsyncMock) as m:
        m.return_value = "I am an AI, here is some text that is definitely not json."

        checks = deterministic_checker.analyze("Some resume text", {})
        payload, model, is_fallback, err = await career_guidance_service.generate_career_guidance(
            resume_text="Some resume text",
            parsed_data={"skills": ["Python"]},
            deterministic_checks=checks,
        )

        assert isinstance(payload, LLMAnalysisPayload)
        assert is_fallback is True
        assert err is not None
        assert model is None


@pytest.mark.asyncio
async def test_career_guidance_timeout_triggers_fallback():
    """Verify that network timeout from Ollama triggers safe fallback."""
    with patch.object(career_guidance_service, "_query_ollama", new_callable=AsyncMock) as m:
        m.side_effect = httpx.TimeoutException("Connection timed out")

        checks = deterministic_checker.analyze("Some resume text", {})
        payload, model, is_fallback, err = await career_guidance_service.generate_career_guidance(
            resume_text="Some resume text",
            parsed_data={"skills": ["Python"]},
            deterministic_checks=checks,
        )

        assert isinstance(payload, LLMAnalysisPayload)
        assert is_fallback is True
        assert err is not None


# ---------------------------------------------------------------------------
# Integration Tests: End-to-End Analysis API
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_candidate_triggers_general_and_target_role_analysis(
    client: AsyncClient,
    mock_ollama_parser,
    mock_career_guidance_llm,
):
    """Verify candidate can trigger general and role-targeted analyses."""
    token = await register_user(client, "cand_m7@example.com", "Jane Candidate")
    res_id = await upload_resume(client, token, make_pdf(), "jane_resume.pdf")

    # 1. Trigger General Analysis (no target role)
    res_gen = await client.post(
        f"/api/v1/resumes/{res_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert res_gen.status_code == 201
    data_gen = res_gen.json()
    assert data_gen["status"] == AnalysisStatus.COMPLETED.value
    assert data_gen["target_role"] is None
    assert data_gen["resume_id"] == res_id
    assert data_gen["resume_sha256"] is not None
    assert data_gen["deterministic_checks"] is not None
    assert data_gen["deterministic_checks"]["word_count"] > 0
    assert data_gen["analysis_data"]["overall_summary"] is not None
    assert len(data_gen["analysis_data"]["strengths"]) >= 1

    # 2. Trigger Target Role Analysis ("Backend Developer")
    res_target = await client.post(
        f"/api/v1/resumes/{res_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "Backend Developer"},
    )
    assert res_target.status_code == 201
    data_target = res_target.json()
    assert data_target["status"] == AnalysisStatus.COMPLETED.value
    assert data_target["target_role"] == "Backend Developer"
    assert data_target["id"] != data_gen["id"]


@pytest.mark.asyncio
async def test_resume_analysis_insufficient_text_rejected(
    client: AsyncClient,
    mock_ollama_parser,
):
    """Verify that resume without usable extracted text returns 422 Unprocessable Content."""
    token = await register_user(client, "scanned_cand@example.com", "Scanned User")
    # Empty page -> no text extracted
    empty_doc = fitz.open()
    empty_doc.new_page()
    empty_bytes = empty_doc.tobytes()
    empty_doc.close()

    res_id = await upload_resume(client, token, empty_bytes, "scanned.pdf")

    res = await client.post(
        f"/api/v1/resumes/{res_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "Backend Developer"},
    )
    assert res.status_code == 422
    assert "sufficient extracted text" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_resume_analysis_concurrency_prevention(
    client: AsyncClient,
    mock_ollama_parser,
    db_session: AsyncSession,
):
    """Verify duplicate in-flight analysis for same resume and role is rejected with 409 Conflict."""
    token = await register_user(client, "concurrent_cand@example.com", "Concurrent User")
    res_id = await upload_resume(client, token, make_pdf(), "concurrent.pdf")

    # Manually insert a PROCESSING record
    stmt = select(Resume).where(Resume.id == uuid.UUID(res_id))
    resume = (await db_session.execute(stmt)).scalar_one()

    in_flight = ResumeAnalysis(
        candidate_id=resume.candidate_id,
        resume_id=resume.id,
        resume_sha256=resume.sha256,
        target_role="Data Scientist",
        status=AnalysisStatus.PROCESSING.value,
        prompt_version="v1.0.0",
        schema_version="v1.0.0",
    )
    db_session.add(in_flight)
    await db_session.commit()

    # Attempt to trigger duplicate analysis
    dup_res = await client.post(
        f"/api/v1/resumes/{res_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "Data Scientist"},
    )
    assert dup_res.status_code == 409
    assert "in progress" in dup_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_resume_analyses_history_and_detail(
    client: AsyncClient,
    mock_ollama_parser,
    mock_career_guidance_llm,
):
    """Verify historical analyses list and detailed retrieval."""
    token = await register_user(client, "history_cand@example.com", "History User")
    res_id = await upload_resume(client, token, make_pdf(), "history.pdf")

    # Run two analyses
    await client.post(
        f"/api/v1/resumes/{res_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "Role A"},
    )
    second = await client.post(
        f"/api/v1/resumes/{res_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "Role B"},
    )
    second_id = second.json()["id"]

    # List analyses for resume
    list_res = await client.get(
        f"/api/v1/resumes/{res_id}/analyses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 2
    assert any(i["target_role"] == "Role A" for i in items)
    assert any(i["target_role"] == "Role B" for i in items)

    # Get detail of second analysis
    detail_res = await client.get(
        f"/api/v1/analyses/{second_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == second_id
    assert detail["target_role"] == "Role B"
    assert detail["deterministic_checks"] is not None
    assert detail["analysis_data"] is not None


@pytest.mark.asyncio
async def test_resume_analysis_retry_endpoint(
    client: AsyncClient,
    mock_ollama_parser,
    mock_career_guidance_llm,
    db_session: AsyncSession,
):
    """Verify only failed analyses can be retried, and successful ones reject retry with 400."""
    token = await register_user(client, "retry_cand@example.com", "Retry User")
    res_id = await upload_resume(client, token, make_pdf(), "retry.pdf")

    created = await client.post(
        f"/api/v1/resumes/{res_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_role": "DevOps Engineer"},
    )
    analysis_id = created.json()["id"]

    # 1. Attempting to retry a COMPLETED analysis -> 400 Bad Request
    bad_retry = await client.post(
        f"/api/v1/analyses/{analysis_id}/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bad_retry.status_code == 400
    assert "only failed analyses can be retried" in bad_retry.json()["detail"].lower()

    # 2. Mark analysis as FAILED in database
    stmt = select(ResumeAnalysis).where(ResumeAnalysis.id == uuid.UUID(analysis_id))
    analysis = (await db_session.execute(stmt)).scalar_one()
    analysis.status = AnalysisStatus.FAILED.value
    analysis.error_message = "Simulated inference failure"
    await db_session.commit()

    # 3. Retry the failed analysis -> 200 OK, becomes COMPLETED
    good_retry = await client.post(
        f"/api/v1/analyses/{analysis_id}/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert good_retry.status_code == 200
    assert good_retry.json()["status"] == AnalysisStatus.COMPLETED.value
    assert good_retry.json()["error_message"] is None


@pytest.mark.asyncio
async def test_resume_analysis_authorization_and_cross_user_isolation(
    client: AsyncClient,
    mock_ollama_parser,
    mock_career_guidance_llm,
):
    """Verify strict candidate ownership: candidate cannot access or analyze another candidate's resume or analysis."""
    token_a = await register_user(client, "user_a@example.com", "User A")
    token_b = await register_user(client, "user_b@example.com", "User B")

    res_a = await upload_resume(client, token_a, make_pdf(), "resume_a.pdf")
    analysis_a_res = await client.post(
        f"/api/v1/resumes/{res_a}/analyze",
        headers={"Authorization": f"Bearer {token_a}"},
        json={},
    )
    analysis_a_id = analysis_a_res.json()["id"]

    # User B attempts to analyze User A's resume -> 404 Not Found
    b_analyze_a = await client.post(
        f"/api/v1/resumes/{res_a}/analyze",
        headers={"Authorization": f"Bearer {token_b}"},
        json={},
    )
    assert b_analyze_a.status_code == 404

    # User B attempts to list analyses for User A's resume -> 404 Not Found
    b_list_a = await client.get(
        f"/api/v1/resumes/{res_a}/analyses",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_list_a.status_code == 404

    # User B attempts to view User A's analysis detail -> 404 Not Found
    b_get_a = await client.get(
        f"/api/v1/analyses/{analysis_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_get_a.status_code == 404

    # User B attempts to retry User A's analysis -> 404 Not Found
    b_retry_a = await client.post(
        f"/api/v1/analyses/{analysis_a_id}/retry",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_retry_a.status_code == 404
