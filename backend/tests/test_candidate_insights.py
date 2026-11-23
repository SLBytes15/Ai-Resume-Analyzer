import io
import uuid
from unittest.mock import AsyncMock, patch
import fitz
import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job import JobStatus
from app.models.organization import OrganizationRole
from app.models.screening import (
    ScreeningInsight,
    ScreeningInsightStatus,
    ScreeningResult,
    ScreeningResultStatus,
    ScreeningRun,
    ScreeningRunStatus,
)
from app.schemas.resume import ParsedResumeData
from app.schemas.screening import (
    CandidateInsightSchema,
    EvidenceGap,
    KeyStrength,
    RelevantProject,
    StrengthCategory,
)
from app.services.candidate_insight_generator import (
    CandidateInsightGenerator,
    candidate_insight_generator,
)
from app.services.evidence_extractor import (
    EvidenceExtractionSchema,
    ExtractedExperienceEntry,
    ExtractedProjectEntry,
    ExtractedSkillItem,
    evidence_extractor,
)


def make_pdf(text: str = "Candidate Resume\nSkills: Python, FastAPI, PostgreSQL\nExperience: 3 years at Acme Corp") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def mock_ollama_parser():
    mock_data = ParsedResumeData(
        full_name="Bob Developer",
        email="bob@example.com",
        phone="+1-555-0188",
        professional_summary="Backend Engineer with 3 years experience in Python and FastAPI",
        skills=["Python", "FastAPI", "PostgreSQL"],
        education=[],
        experience=[{"role": "Backend Engineer", "company": "Tech Corp", "years": 3, "description": "Built APIs"}],
        projects=[{"name": "E-Commerce Backend", "technologies": ["Python", "FastAPI"], "description": "REST API"}],
        certifications=[],
    )
    with patch("app.services.resume_service.llm_parser.parse_resume", new_callable=AsyncMock) as m:
        m.return_value = mock_data
        yield m


@pytest.fixture
def mock_evidence_extractor():
    mock_evidence = EvidenceExtractionSchema(
        skills=[
            ExtractedSkillItem(skill="Python", canonical_skill="Python", evidence="3 years experience in Python", confidence=1.0),
            ExtractedSkillItem(skill="FastAPI", canonical_skill="FastAPI", evidence="Built APIs in FastAPI", confidence=1.0),
            ExtractedSkillItem(skill="PostgreSQL", canonical_skill="PostgreSQL", evidence="Database design in PostgreSQL", confidence=0.9),
        ],
        experience=[ExtractedExperienceEntry(role="Backend Engineer", company="Tech Corp", years=3.0)],
        projects=[ExtractedProjectEntry(name="E-Commerce API", technologies=["Python", "FastAPI"], description="Built scalable REST API")],
        inferred_years_of_experience=3.0,
        extraction_notes="Extracted from submitted resume text",
    )
    with patch.object(evidence_extractor, "extract_evidence", new_callable=AsyncMock) as m:
        m.return_value = mock_evidence
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


async def create_job(client: AsyncClient, token: str, org_id: str, title: str = "Lead Backend Engineer") -> str:
    res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={
            "title": title,
            "description": "Looking for lead backend engineer",
            "workplace_type": "REMOTE",
            "employment_type": "FULL_TIME",
            "experience_min": 2,
            "experience_max": 5,
            "required_skills": ["Python", "FastAPI"],
            "preferred_skills": ["Docker", "PostgreSQL"],
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


async def upload_resume(client: AsyncClient, token: str, content: bytes, filename: str = "bob_resume.pdf") -> str:
    await client.post(
        "/api/v1/candidates/me/profile",
        json={"phone": "+1234567890", "location": "Bengaluru", "headline": "Backend Engineer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    res = await client.post(
        "/api/v1/resumes/upload",
        files={"file": (filename, io.BytesIO(content), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    return res.json()["id"]


# =========================================================================
# 1. UNIT TESTS: CandidateInsightGenerator Service
# =========================================================================

def test_deterministic_fallback_insight_structure():
    """Verify deterministic fallback produces complete, valid insight schema without LLM."""
    generator = CandidateInsightGenerator()

    job_criteria = {
        "title": "Backend Engineer",
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["Docker"],
        "experience_min": 2,
    }
    score_data = {
        "total_score": 85.0,
        "required_skill_score": 100.0,
        "preferred_skill_score": 0.0,
        "experience_score": 100.0,
        "matched_skills": [
            {"skill": "Python", "canonical_skill": "Python", "evidence": "Built Python services"},
            {"skill": "FastAPI", "canonical_skill": "FastAPI", "evidence": "Developed REST APIs in FastAPI"},
        ],
        "preferred_skill_matches": [],
        "missing_evidence": [
            {"skill": "Docker", "canonical_skill": "Docker", "reason": "Not evidenced in resume"}
        ],
        "experience_assessment": {
            "status": "VERIFIED_SUFFICIENT",
            "verified_years": 3.0,
            "required_min_years": 2,
        },
    }
    extracted_projects = [
        {"name": "E-Commerce Service", "technologies": ["Python", "FastAPI"], "description": "REST API service"}
    ]
    extracted_experience = [
        {"role": "Backend Developer", "company": "Tech Corp", "years": 3.0}
    ]

    fallback = generator.generate_deterministic_fallback(
        job_criteria=job_criteria,
        score_data=score_data,
        extracted_projects=extracted_projects,
        extracted_experience=extracted_experience,
    )

    assert isinstance(fallback, CandidateInsightSchema)
    assert "Backend Engineer" in fallback.summary
    assert "85.0" in fallback.summary
    assert len(fallback.key_strengths) >= 1
    assert any("Python" in s.title for s in fallback.key_strengths)
    assert len(fallback.relevant_projects) == 1
    assert fallback.relevant_projects[0].project_name == "E-Commerce Service"
    assert "Python" in fallback.relevant_projects[0].relevant_requirements
    assert len(fallback.evidence_gaps) == 1
    assert fallback.evidence_gaps[0].requirement == "Docker"
    assert "85.0" in fallback.score_explanation


@pytest.mark.asyncio
async def test_insight_generator_valid_llm_response():
    """Verify valid LLM response parsing and schema validation."""
    mock_llm_json = """{
      "summary": "Candidate shows strong alignment with core backend requirements.",
      "key_strengths": [
        {
          "title": "Backend API Development",
          "description": "Extensive experience building APIs in FastAPI and Python.",
          "supporting_evidence": ["Developed APIs in FastAPI"],
          "category": "EXPERIENCE"
        }
      ],
      "relevant_projects": [
        {
          "project_name": "API Gateway",
          "description": "Built using FastAPI and Python.",
          "relevant_requirements": ["Python", "FastAPI"],
          "supporting_evidence": ["REST API project"]
        }
      ],
      "evidence_gaps": [
        {
          "requirement": "Docker",
          "explanation": "No Docker evidence was identified in the submitted resume text."
        }
      ],
      "uncertainties": [],
      "score_explanation": "Score is supported by evidenced required skills."
    }"""

    with patch.object(candidate_insight_generator, "_query_ollama", new_callable=AsyncMock) as m_query:
        m_query.return_value = mock_llm_json

        insight, model_used, is_fallback = await candidate_insight_generator.generate_insight(
            job_criteria={"title": "Backend Engineer", "required_skills": ["Python", "FastAPI"]},
            score_data={"total_score": 85.0},
            extracted_projects=[],
            extracted_experience=[],
            resume_text="Sample resume text",
        )

        assert isinstance(insight, CandidateInsightSchema)
        assert model_used == candidate_insight_generator.primary_model
        assert not is_fallback
        assert len(insight.key_strengths) == 1
        assert insight.key_strengths[0].category == StrengthCategory.EXPERIENCE
        assert len(insight.evidence_gaps) == 1
        assert insight.evidence_gaps[0].requirement == "Docker"


@pytest.mark.asyncio
async def test_insight_generator_malformed_json_triggers_fallback():
    """Verify malformed JSON from LLM triggers deterministic fallback cleanly."""
    with patch.object(candidate_insight_generator, "_query_ollama", new_callable=AsyncMock) as m_query:
        # Return broken JSON
        m_query.return_value = "Here is your insight: {broken_json..."

        insight, model_used, is_fallback = await candidate_insight_generator.generate_insight(
            job_criteria={"title": "Backend Engineer", "required_skills": ["Python", "FastAPI"]},
            score_data={"total_score": 85.0, "matched_skills": [{"skill": "Python"}]},
            extracted_projects=[],
            extracted_experience=[],
            resume_text="Sample resume text",
        )

        assert isinstance(insight, CandidateInsightSchema)
        assert is_fallback
        assert model_used == "deterministic-fallback"
        assert "85.0" in insight.summary


@pytest.mark.asyncio
async def test_insight_generator_timeout_triggers_fallback():
    """Verify model timeout triggers deterministic fallback gracefully."""
    with patch.object(candidate_insight_generator, "_query_ollama", new_callable=AsyncMock) as m_query:
        m_query.side_effect = httpx.TimeoutException("Ollama request timed out after 25s")

        insight, model_used, is_fallback = await candidate_insight_generator.generate_insight(
            job_criteria={"title": "Backend Engineer", "required_skills": ["Python"]},
            score_data={"total_score": 90.0, "matched_skills": [{"skill": "Python"}]},
            extracted_projects=[],
            extracted_experience=[],
            resume_text="Sample resume text",
        )

        assert isinstance(insight, CandidateInsightSchema)
        assert is_fallback
        assert model_used == "deterministic-fallback"


# =========================================================================
# 2. INTEGRATION TESTS: End-to-End Insight Generation, API & Persistence
# =========================================================================

@pytest.mark.asyncio
async def test_end_to_end_screening_generates_and_persists_insight(
    client: AsyncClient,
    mock_ollama_parser,
    mock_evidence_extractor,
):
    """Verify full screening run generates and persists CandidateInsight alongside results."""
    # 1. Setup recruiter & job
    recruiter_token = await register_user(client, "insight_recruiter@example.com", "Insight Recruiter")
    org_id = await create_org(client, recruiter_token, "Insight Org", "insight-org")
    job_id = await create_job(client, recruiter_token, org_id, "Cloud Engineer")
    await publish_job(client, recruiter_token, org_id, job_id)

    # 2. Setup candidate & apply
    cand_token = await register_user(client, "cand_insight@example.com", "Insight Candidate")
    pdf_bytes = make_pdf("Candidate: Python, FastAPI\nProject: Built E-Commerce API in Python and FastAPI")
    res_id = await upload_resume(client, cand_token, pdf_bytes, "insight_resume.pdf")

    app_res = await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": res_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert app_res.status_code == 201

    # 3. Recruiter triggers screening
    trigger_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/screenings",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert trigger_res.status_code in (200, 201, 202)
    run_id = trigger_res.json()["id"]

    # 4. List results: verify insight summary is populated in list
    results_res = await client.get(
        f"/api/v1/organizations/{org_id}/screenings/{run_id}/results",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert results_res.status_code == 200
    results = results_res.json()["items"]
    assert len(results) == 1
    assert results[0]["insight_summary"] is not None
    assert "Cloud Engineer" in results[0]["insight_summary"]
    result_id = results[0]["id"]

    # 5. Get detail: verify full insight object is returned
    detail_res = await client.get(
        f"/api/v1/organizations/{org_id}/screenings/results/{result_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["insight"] is not None
    insight = detail["insight"]
    assert insight["status"] in (ScreeningInsightStatus.COMPLETED.value, ScreeningInsightStatus.FAILED.value)
    assert "summary" in insight["insight_data"]
    assert "key_strengths" in insight["insight_data"]
    assert "relevant_projects" in insight["insight_data"]
    assert "score_explanation" in insight["insight_data"]


@pytest.mark.asyncio
async def test_insight_failure_preserves_screening_score(
    client: AsyncClient,
    mock_ollama_parser,
    mock_evidence_extractor,
):
    """Verify that if insight generation fails, screening score remains intact and fallback is preserved."""
    recruiter_token = await register_user(client, "pres_recruiter@example.com", "Preserve Recruiter")
    org_id = await create_org(client, recruiter_token, "Preserve Org", "pres-org")
    job_id = await create_job(client, recruiter_token, org_id, "DevOps Engineer")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand_token = await register_user(client, "cand_pres@example.com", "Preserve Candidate")
    res_id = await upload_resume(client, cand_token, make_pdf("Python, FastAPI"), "pres_resume.pdf")
    await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": res_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )

    # Force candidate_insight_generator.generate_insight to raise an error
    with patch.object(candidate_insight_generator, "generate_insight", side_effect=RuntimeError("Simulated LLM crash")):
        trigger_res = await client.post(
            f"/api/v1/organizations/{org_id}/jobs/{job_id}/screenings",
            headers={"Authorization": f"Bearer {recruiter_token}"},
        )
        assert trigger_res.status_code in (200, 201, 202)
        run_id = trigger_res.json()["id"]

    # Verify that the screening result and score are completely intact!
    results_res = await client.get(
        f"/api/v1/organizations/{org_id}/screenings/{run_id}/results",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    item = results_res.json()["items"][0]
    assert item["total_score"] is not None
    assert item["total_score"] > 0
    assert item["required_skill_score"] == 100.0

    # Verify insight is saved as FAILED with deterministic fallback
    detail_res = await client.get(
        f"/api/v1/organizations/{org_id}/screenings/results/{item['id']}",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    detail = detail_res.json()
    assert detail["insight"] is not None
    assert detail["insight"]["status"] == ScreeningInsightStatus.FAILED.value
    assert "Simulated LLM crash" in detail["insight"]["error_message"]
    assert detail["insight"]["insight_data"]["summary"] is not None


@pytest.mark.asyncio
async def test_insight_retry_endpoint(
    client: AsyncClient,
    mock_ollama_parser,
    mock_evidence_extractor,
):
    """Verify recruiter can trigger manual insight retry and score is not modified."""
    recruiter_token = await register_user(client, "retry_recruiter@example.com", "Retry Recruiter")
    org_id = await create_org(client, recruiter_token, "Retry Org", "retry-org")
    job_id = await create_job(client, recruiter_token, org_id, "Platform Engineer")
    await publish_job(client, recruiter_token, org_id, job_id)

    cand_token = await register_user(client, "cand_retry@example.com", "Retry Candidate")
    res_id = await upload_resume(client, cand_token, make_pdf("Python, FastAPI"), "retry_resume.pdf")
    await client.post(
        f"/api/v1/jobs/{job_id}/applications",
        json={"resume_id": res_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )

    trigger_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/screenings",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    run_id = trigger_res.json()["id"]

    results_res = await client.get(
        f"/api/v1/organizations/{org_id}/screenings/{run_id}/results",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    result_id = results_res.json()["items"][0]["id"]
    initial_score = results_res.json()["items"][0]["total_score"]

    # Trigger insight retry
    retry_res = await client.post(
        f"/api/v1/organizations/{org_id}/screenings/results/{result_id}/insight/retry",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert retry_res.status_code == 200
    retried_insight = retry_res.json()
    assert retried_insight["status"] == ScreeningInsightStatus.COMPLETED.value
    assert retried_insight["screening_result_id"] == result_id

    # Verify score was NOT altered by retry
    verify_res = await client.get(
        f"/api/v1/organizations/{org_id}/screenings/results/{result_id}",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert verify_res.json()["total_score"] == initial_score


@pytest.mark.asyncio
async def test_insight_authorization_and_isolation(
    client: AsyncClient,
    mock_ollama_parser,
    mock_evidence_extractor,
):
    """Verify organization role enforcement and cross-tenant isolation on insight retry."""
    fallback = candidate_insight_generator.generate_deterministic_fallback(
        job_criteria={"title": "Job A", "required_skills": ["Python"]},
        score_data={"total_score": 85.0},
        extracted_projects=[],
        extracted_experience=[],
    )
    with patch.object(candidate_insight_generator, "generate_insight", new_callable=AsyncMock) as m_gen:
        m_gen.return_value = (fallback, "qwen3:4b", False)
        # Org A
        owner_a = await register_user(client, "owner_a@example.com", "Owner A")
        viewer_a = await register_user(client, "viewer_a@example.com", "Viewer A")
        org_a = await create_org(client, owner_a, "Org A", "org-a-insights")
        job_a = await create_job(client, owner_a, org_a, "Job A")
        await publish_job(client, owner_a, org_a, job_a)

        # Add viewer to Org A
        await client.post(
            f"/api/v1/recruiter/organizations/{org_a}/members",
            json={"email": "viewer_a@example.com", "role": OrganizationRole.VIEWER.value},
            headers={"Authorization": f"Bearer {owner_a}"},
        )

        # Candidate apply & screen
        cand_token = await register_user(client, "cand_iso@example.com", "Iso Candidate")
        res_id = await upload_resume(client, cand_token, make_pdf("Python"), "iso.pdf")
        await client.post(
            f"/api/v1/jobs/{job_a}/applications",
            json={"resume_id": res_id},
            headers={"Authorization": f"Bearer {cand_token}"},
        )

        trig = await client.post(
            f"/api/v1/organizations/{org_a}/jobs/{job_a}/screenings",
            headers={"Authorization": f"Bearer {owner_a}"},
        )
        run_id = trig.json()["id"]
        res_list = await client.get(
            f"/api/v1/organizations/{org_a}/screenings/{run_id}/results",
            headers={"Authorization": f"Bearer {owner_a}"},
        )
        result_id = res_list.json()["items"][0]["id"]

        # 1. Viewer cannot retry insight -> 403 Forbidden
        viewer_retry = await client.post(
            f"/api/v1/organizations/{org_a}/screenings/results/{result_id}/insight/retry",
            headers={"Authorization": f"Bearer {viewer_a}"},
        )
        assert viewer_retry.status_code == 403

        # 2. Org B recruiter cannot access or retry Org A's result insight
        recruiter_b = await register_user(client, "recruiter_b@example.com", "Recruiter B")
        org_b = await create_org(client, recruiter_b, "Org B", "org-b-insights")

        cross_retry = await client.post(
            f"/api/v1/organizations/{org_b}/screenings/results/{result_id}/insight/retry",
            headers={"Authorization": f"Bearer {recruiter_b}"},
        )
        assert cross_retry.status_code in (403, 404)
