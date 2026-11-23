import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from app.models.job import EmploymentType, JobStatus, WorkplaceType


async def create_user_and_token(
    client: AsyncClient, email: str, full_name: str = "Test User"
) -> str:
    """Helper creating user and returning JWT token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "full_name": full_name},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    return res.json()["access_token"]


async def create_org(client: AsyncClient, token: str, name: str, slug: str) -> str:
    """Helper creating organization and returning its ID."""
    res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": name, "slug": slug},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    return res.json()["id"]


# ==========================================
# 1. Job Creation Tests
# ==========================================


@pytest.mark.asyncio
async def test_authorized_recruiter_creates_draft_job(client: AsyncClient):
    token = await create_user_and_token(client, "recruiter1@acme.com", "Recruiter One")
    org_id = await create_org(client, token, "Acme Corp", "acme-corp")

    job_payload = {
        "title": "Senior Python Backend Engineer",
        "department": "Engineering",
        "description": "Design and maintain high-performance distributed backend services.",
        "responsibilities": "Write clean async code, maintain CI/CD pipelines.",
        "qualifications": "5+ years Python and PostgreSQL experience.",
        "location": "Bengaluru, India",
        "workplace_type": "HYBRID",
        "employment_type": "FULL_TIME",
        "experience_min": 4,
        "experience_max": 8,
        "salary_min": 2500000,
        "salary_max": 4000000,
        "salary_currency": "INR",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "preferred_skills": ["Docker", "Kubernetes", "AWS"],
    }

    res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json=job_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Senior Python Backend Engineer"
    assert data["status"] == "DRAFT"
    assert data["published_at"] is None
    assert data["organization_id"] == org_id
    assert data["required_skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert data["preferred_skills"] == ["Docker", "Kubernetes", "AWS"]
    assert data["slug"] is not None


@pytest.mark.asyncio
async def test_job_creation_missing_required_fields_rejected(client: AsyncClient):
    token = await create_user_and_token(client, "recruiter2@acme.com", "Recruiter Two")
    org_id = await create_org(client, token, "Beta Corp", "beta-corp")

    # Missing title
    res1 = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"description": "Some description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 422

    # Missing description
    res2 = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Software Engineer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 422

    # Empty title or whitespace
    res3 = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "   ", "description": "Valid description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res3.status_code == 422


@pytest.mark.asyncio
async def test_job_creation_invalid_salary_range_rejected(client: AsyncClient):
    token = await create_user_and_token(client, "recruiter3@acme.com", "Recruiter Three")
    org_id = await create_org(client, token, "Gamma Corp", "gamma-corp")

    # salary_min > salary_max
    res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={
            "title": "DevOps Engineer",
            "description": "Cloud infra",
            "salary_min": 5000000,
            "salary_max": 2000000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_job_creation_invalid_experience_range_rejected(client: AsyncClient):
    token = await create_user_and_token(client, "recruiter4@acme.com", "Recruiter Four")
    org_id = await create_org(client, token, "Delta Corp", "delta-corp")

    # experience_min > experience_max
    res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={
            "title": "QA Engineer",
            "description": "Test automation",
            "experience_min": 5,
            "experience_max": 2,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_job_creation_skill_validation(client: AsyncClient):
    token = await create_user_and_token(client, "recruiter5@acme.com", "Recruiter Five")
    org_id = await create_org(client, token, "Epsilon Corp", "epsilon-corp")

    # Overlapping skills in required and preferred
    res_overlap = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={
            "title": "Full Stack Dev",
            "description": "Web apps",
            "required_skills": ["React", "Python"],
            "preferred_skills": ["python", "AWS"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_overlap.status_code == 422

    # Empty string skill
    res_empty_skill = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={
            "title": "Full Stack Dev",
            "description": "Web apps",
            "required_skills": ["React", "   "],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_empty_skill.status_code == 422

    # Normalization deduplicates within list
    res_dedup = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={
            "title": "Full Stack Dev",
            "description": "Web apps",
            "required_skills": ["Python", "python", "  Python  "],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_dedup.status_code == 201
    assert res_dedup.json()["required_skills"] == ["Python"]


@pytest.mark.asyncio
async def test_viewer_cannot_create_jobs(client: AsyncClient):
    owner_token = await create_user_and_token(client, "owner.view@acme.com", "Owner")
    org_id = await create_org(client, owner_token, "Zeta Corp", "zeta-corp")

    # Add user as VIEWER
    viewer_token = await create_user_and_token(client, "viewer@acme.com", "Viewer")
    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "viewer@acme.com", "role": "VIEWER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Viewer attempts to create job
    res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Illegal Job", "description": "Should fail"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res.status_code == 403


# ==========================================
# 2. Job Management & Lifecycle Tests
# ==========================================


@pytest.mark.asyncio
async def test_recruiter_edits_job_and_viewer_cannot_edit(client: AsyncClient):
    owner_token = await create_user_and_token(client, "owner.edit@acme.com", "Owner")
    org_id = await create_org(client, owner_token, "Eta Corp", "eta-corp")

    # Recruiter member
    rec_token = await create_user_and_token(client, "rec.edit@acme.com", "Recruiter")
    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "rec.edit@acme.com", "role": "RECRUITER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Viewer member
    viewer_token = await create_user_and_token(client, "view.edit@acme.com", "Viewer")
    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "view.edit@acme.com", "role": "VIEWER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Recruiter creates job
    create_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Initial Title", "description": "Initial desc"},
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    job_id = create_res.json()["id"]

    # Recruiter edits job
    patch_res = await client.patch(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}",
        json={"title": "Updated Title", "location": "Remote"},
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Title"
    assert patch_res.json()["location"] == "Remote"

    # Viewer attempts to edit job
    viewer_patch = await client.patch(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}",
        json={"title": "Viewer Hack"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_patch.status_code == 403

    # Viewer CAN view the job
    viewer_get = await client.get(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_get.status_code == 200
    assert viewer_get.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_lifecycle_transitions_and_rules(client: AsyncClient):
    token = await create_user_and_token(client, "lifecycle@acme.com", "Lifecycle Recruiter")
    org_id = await create_org(client, token, "Theta Corp", "theta-corp")

    # 1. Starts as DRAFT
    create_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Lifecycle Engineer", "description": "Transitions check"},
        headers={"Authorization": f"Bearer {token}"},
    )
    job_id = create_res.json()["id"]
    assert create_res.json()["status"] == "DRAFT"
    assert create_res.json()["published_at"] is None

    # Invalid: Cannot close a DRAFT job directly
    close_draft = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/close",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert close_draft.status_code == 409

    # Invalid: Cannot archive a DRAFT job directly
    archive_draft = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/archive",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert archive_draft.status_code == 409

    # 2. Publish DRAFT job -> PUBLISHED
    pub_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "PUBLISHED"
    assert pub_data["published_at"] is not None
    original_published_at = pub_data["published_at"]

    # Invalid: Cannot republish an already PUBLISHED job
    pub_again = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pub_again.status_code == 409

    # Edit published job preserves original published_at
    edit_res = await client.patch(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}",
        json={"department": "Platform"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["published_at"] == original_published_at

    # 3. Close PUBLISHED job -> CLOSED
    close_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/close",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"

    # Invalid: Cannot republish CLOSED job
    pub_closed = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pub_closed.status_code == 409

    # 4. Archive CLOSED job -> ARCHIVED
    arch_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/archive",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "ARCHIVED"

    # Invalid: Cannot modify an ARCHIVED job
    arch_edit = await client.patch(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}",
        json={"title": "Should Not Edit"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert arch_edit.status_code == 409

    # Invalid: Cannot re-archive or re-close ARCHIVED job
    arch_again = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/archive",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert arch_again.status_code == 409


# ==========================================
# 3. Public Discovery & Filtering Tests
# ==========================================


@pytest.mark.asyncio
async def test_public_discovery_rules(client: AsyncClient):
    token = await create_user_and_token(client, "discovery@acme.com", "Discovery Recruiter")
    org_id = await create_org(client, token, "Iota Corp", "iota-corp")

    # Create Draft, Published, Closed, Archived jobs
    # 1. Draft
    draft_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Draft Secret Role", "description": "Internal only"},
        headers={"Authorization": f"Bearer {token}"},
    )
    draft_id = draft_res.json()["id"]

    # 2. Published
    pub_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={
            "title": "Public Software Engineer",
            "department": "Engineering",
            "description": "Building next-gen AI tools",
            "location": "Bengaluru",
            "workplace_type": "REMOTE",
            "employment_type": "FULL_TIME",
            "required_skills": ["Python", "FastAPI"],
            "preferred_skills": ["PostgreSQL"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pub_id = pub_res.json()["id"]
    await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{pub_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )

    # 3. Closed
    closed_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Closed Role", "description": "No longer open"},
        headers={"Authorization": f"Bearer {token}"},
    )
    closed_id = closed_res.json()["id"]
    await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{closed_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{closed_id}/close",
        headers={"Authorization": f"Bearer {token}"},
    )

    # 4. Archived
    arch_res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Archived Role", "description": "Old history"},
        headers={"Authorization": f"Bearer {token}"},
    )
    arch_id = arch_res.json()["id"]
    await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{arch_id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{arch_id}/close",
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{arch_id}/archive",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Public list: only PUBLISHED jobs returned
    public_res = await client.get("/api/v1/jobs")
    assert public_res.status_code == 200
    public_jobs = public_res.json()
    assert len(public_jobs) == 1
    assert public_jobs[0]["id"] == pub_id
    assert public_jobs[0]["organization_name"] == "Iota Corp"
    # Ensure sensitive recruiter metadata not leaked
    assert "created_by" not in public_jobs[0]

    # Individual public lookups
    # Published: 200 OK
    pub_single = await client.get(f"/api/v1/jobs/{pub_id}")
    assert pub_single.status_code == 200
    assert pub_single.json()["title"] == "Public Software Engineer"

    # Draft: 404
    draft_single = await client.get(f"/api/v1/jobs/{draft_id}")
    assert draft_single.status_code == 404

    # Closed: 404
    closed_single = await client.get(f"/api/v1/jobs/{closed_id}")
    assert closed_single.status_code == 404

    # Archived: 404
    arch_single = await client.get(f"/api/v1/jobs/{arch_id}")
    assert arch_single.status_code == 404


@pytest.mark.asyncio
async def test_search_filtering_and_pagination(client: AsyncClient):
    token = await create_user_and_token(client, "filter@acme.com", "Filter Recruiter")
    org_id = await create_org(client, token, "Kappa Corp", "kappa-corp")

    # Seed 3 published jobs
    jobs_data = [
        {
            "title": "Backend Python Developer",
            "department": "Core",
            "description": "High throughput services in Python",
            "location": "Bengaluru",
            "workplace_type": "HYBRID",
            "employment_type": "FULL_TIME",
            "required_skills": ["Python", "FastAPI"],
        },
        {
            "title": "Frontend React Specialist",
            "department": "UI/UX",
            "description": "Interactive web dashboards in React and TypeScript",
            "location": "Mumbai",
            "workplace_type": "REMOTE",
            "employment_type": "CONTRACT",
            "required_skills": ["React", "TypeScript"],
        },
        {
            "title": "Machine Learning Engineer",
            "department": "AI Research",
            "description": "Deep learning models using PyTorch and Python",
            "location": "Bengaluru",
            "workplace_type": "ONSITE",
            "employment_type": "FULL_TIME",
            "required_skills": ["Python", "PyTorch"],
        },
    ]

    for j in jobs_data:
        res = await client.post(
            f"/api/v1/organizations/{org_id}/jobs",
            json=j,
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            f"/api/v1/organizations/{org_id}/jobs/{res.json()['id']}/publish",
            headers={"Authorization": f"Bearer {token}"},
        )

    # 1. Filter by keyword: "python" (matches Backend and ML)
    res_kw = await client.get("/api/v1/jobs?keyword=python")
    assert res_kw.status_code == 200
    assert len(res_kw.json()) == 2

    # 2. Filter by location: "Bengaluru"
    res_loc = await client.get("/api/v1/jobs?location=Bengaluru")
    assert res_loc.status_code == 200
    assert len(res_loc.json()) == 2

    # 3. Filter by workplace_type: "REMOTE"
    res_wp = await client.get("/api/v1/jobs?workplace_type=REMOTE")
    assert res_wp.status_code == 200
    assert len(res_wp.json()) == 1
    assert res_wp.json()[0]["title"] == "Frontend React Specialist"

    # 4. Filter by employment_type: "CONTRACT"
    res_emp = await client.get("/api/v1/jobs?employment_type=CONTRACT")
    assert res_emp.status_code == 200
    assert len(res_emp.json()) == 1

    # 5. Filter by required skill: "pytorch" (case-insensitive JSONB)
    res_skill = await client.get("/api/v1/jobs?skill=pytorch")
    assert res_skill.status_code == 200
    assert len(res_skill.json()) == 1
    assert res_skill.json()[0]["title"] == "Machine Learning Engineer"

    # 6. Pagination: limit=1, offset=0 and offset=1
    page1 = await client.get("/api/v1/jobs?limit=1&offset=0")
    assert len(page1.json()) == 1
    assert page1.headers["X-Total-Count"] == "3"

    page2 = await client.get("/api/v1/jobs?limit=1&offset=1")
    assert len(page2.json()) == 1
    assert page1.json()[0]["id"] != page2.json()[0]["id"]


# ==========================================
# 4. Tenant Isolation Tests
# ==========================================


@pytest.mark.asyncio
async def test_cross_tenant_isolation(client: AsyncClient):
    # Org Alpha with Recruiter A
    token_a = await create_user_and_token(client, "rec_a@alpha.com", "Recruiter Alpha")
    org_a = await create_org(client, token_a, "Org Alpha", "org-alpha-sec")

    # Org Beta with Recruiter B
    token_b = await create_user_and_token(client, "rec_b@beta.com", "Recruiter Beta")
    org_b = await create_org(client, token_b, "Org Beta", "org-beta-sec")

    # Org A creates a draft job
    res_job_a = await client.post(
        f"/api/v1/organizations/{org_a}/jobs",
        json={"title": "Alpha Confidential Job", "description": "Internal secret"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    job_a_id = res_job_a.json()["id"]

    # 1. Recruiter B cannot view Org A's private job list (403 Forbidden)
    res_list = await client.get(
        f"/api/v1/organizations/{org_a}/jobs",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_list.status_code == 403

    # 2. Recruiter B cannot retrieve Org A's job via Org A route (403 Forbidden)
    res_get_a = await client.get(
        f"/api/v1/organizations/{org_a}/jobs/{job_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_get_a.status_code == 403

    # 3. Recruiter B cannot retrieve Org A's job via Org B route (404 Not Found)
    res_get_b = await client.get(
        f"/api/v1/organizations/{org_b}/jobs/{job_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_get_b.status_code == 404

    # 4. Recruiter B cannot edit Org A's job via Org A route (403 Forbidden)
    res_edit_a = await client.patch(
        f"/api/v1/organizations/{org_a}/jobs/{job_a_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_edit_a.status_code == 403

    # 5. Recruiter B cannot edit Org A's job via Org B route (404 Not Found)
    res_edit_b = await client.patch(
        f"/api/v1/organizations/{org_b}/jobs/{job_a_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_edit_b.status_code == 404

    # 6. Recruiter B cannot publish Org A's job (403 or 404)
    res_pub_a = await client.post(
        f"/api/v1/organizations/{org_a}/jobs/{job_a_id}/publish",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_pub_a.status_code == 403

    res_pub_b = await client.post(
        f"/api/v1/organizations/{org_b}/jobs/{job_a_id}/publish",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_pub_b.status_code == 404

    # 7. Recruiter B cannot close or archive Org A's job
    res_close = await client.post(
        f"/api/v1/organizations/{org_a}/jobs/{job_a_id}/close",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_close.status_code == 403

    res_arch = await client.post(
        f"/api/v1/organizations/{org_a}/jobs/{job_a_id}/archive",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_arch.status_code == 403


@pytest.mark.asyncio
async def test_admin_and_owner_full_job_management(client: AsyncClient):
    owner_token = await create_user_and_token(client, "bigboss@acme.com", "Big Boss")
    org_id = await create_org(client, owner_token, "Owner Admin Org", "owner-admin-org")

    # Add user as ADMIN
    admin_token = await create_user_and_token(client, "lead.admin@acme.com", "Lead Admin")
    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "lead.admin@acme.com", "role": "ADMIN"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # 1. Admin creates draft job
    res = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Admin Role", "description": "Created by Admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201
    job_id = res.json()["id"]

    # 2. Admin edits job
    res_edit = await client.patch(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}",
        json={"location": "Delhi"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_edit.status_code == 200
    assert res_edit.json()["location"] == "Delhi"

    # 3. Admin publishes job
    res_pub = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_pub.status_code == 200
    assert res_pub.json()["status"] == "PUBLISHED"

    # 4. Owner closes job
    res_close = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/close",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_close.status_code == 200
    assert res_close.json()["status"] == "CLOSED"

    # 5. Admin archives job
    res_arch = await client.post(
        f"/api/v1/organizations/{org_id}/jobs/{job_id}/archive",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_arch.status_code == 200
    assert res_arch.json()["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_negative_values_rejected(client: AsyncClient):
    token = await create_user_and_token(client, "negative@acme.com", "Negative Tester")
    org_id = await create_org(client, token, "Negative Org", "negative-org")

    # Negative experience_min
    res1 = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Negative Exp", "description": "Invalid", "experience_min": -1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 422

    # Negative salary_min
    res2 = await client.post(
        f"/api/v1/organizations/{org_id}/jobs",
        json={"title": "Negative Sal", "description": "Invalid", "salary_min": -500},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 422


@pytest.mark.asyncio
async def test_database_constraints_direct(db_session):
    from sqlalchemy.exc import IntegrityError
    from app.models.job import Job
    from app.models.organization import Organization
    from app.models.user import User

    # Create dummy org and user
    user = User(email="db_test@acme.com", password_hash="pw", full_name="DB Tester")
    org = Organization(name="DB Direct Org", slug="db-direct-org")
    db_session.add_all([user, org])
    await db_session.commit()
    await db_session.refresh(org)
    await db_session.refresh(user)
    saved_org_id = org.id

    # 1. Job without organization_id must violate NOT NULL / FK
    with pytest.raises(IntegrityError):
        bad_job = Job(
            organization_id=None,  # Not allowed
            title="No Org Job",
            description="Should fail",
        )
        db_session.add(bad_job)
        await db_session.commit()
    await db_session.rollback()

    # 2. Job with experience_min > experience_max must violate CheckConstraint
    with pytest.raises(IntegrityError):
        bad_exp = Job(
            organization_id=saved_org_id,
            title="Bad Exp",
            description="Should fail",
            experience_min=10,
            experience_max=2,
        )
        db_session.add(bad_exp)
        await db_session.commit()
    await db_session.rollback()

    # 3. Job with invalid status must violate CheckConstraint
    with pytest.raises(IntegrityError):
        bad_status = Job(
            organization_id=saved_org_id,
            title="Bad Status",
            description="Should fail",
            status="INVALID_STATUS",
        )
        db_session.add(bad_status)
        await db_session.commit()
    await db_session.rollback()

