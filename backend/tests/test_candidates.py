import pytest
from httpx import AsyncClient


async def create_user_and_token(
    client: AsyncClient, email: str, full_name: str, password: str = "SecurePass123!"
):
    """Helper to register user and return token + user data."""
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert res.status_code == 201, res.text
    data = res.json()
    return data["access_token"], data["user"]


@pytest.mark.asyncio
async def test_candidate_profile_create_and_retrieve(client: AsyncClient):
    """Test creating and retrieving candidate profile."""
    token, user = await create_user_and_token(client, "candidate1@example.com", "Candidate One")

    # Profile not yet created -> 404
    res_get = await client.get(
        "/api/v1/candidates/me/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_get.status_code == 404

    # Create profile
    payload = {
        "phone": "+1-555-0199",
        "location": "San Francisco, CA",
        "headline": "Senior Backend Engineer",
        "professional_summary": "Experienced Python & PostgreSQL specialist.",
    }
    res_post = await client.post(
        "/api/v1/candidates/me/profile",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_post.status_code == 201, res_post.text
    data = res_post.json()
    assert data["phone"] == "+1-555-0199"
    assert data["headline"] == "Senior Backend Engineer"
    assert data["email"] == "candidate1@example.com"
    assert data["full_name"] == "Candidate One"

    # Retrieve profile
    res_get2 = await client.get(
        "/api/v1/candidates/me/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_get2.status_code == 200
    assert res_get2.json()["headline"] == "Senior Backend Engineer"


@pytest.mark.asyncio
async def test_duplicate_profile_creation_rejected(client: AsyncClient):
    """Test creating a second candidate profile for the same user returns 409 Conflict."""
    token, _ = await create_user_and_token(client, "dup.cand@example.com", "Dup Cand")

    payload = {"headline": "First Profile"}
    res1 = await client.post(
        "/api/v1/candidates/me/profile",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201

    res2 = await client.post(
        "/api/v1/candidates/me/profile",
        json={"headline": "Second Profile Attempt"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_candidate_profile_patch_update(client: AsyncClient):
    """Test updating existing candidate profile fields."""
    token, _ = await create_user_and_token(client, "patch.cand@example.com", "Patch Cand")

    await client.post(
        "/api/v1/candidates/me/profile",
        json={"headline": "Initial Headline", "location": "Austin, TX"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Patch location and summary
    res_patch = await client.patch(
        "/api/v1/candidates/me/profile",
        json={"location": "Seattle, WA", "headline": "Staff Engineer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_patch.status_code == 200
    data = res_patch.json()
    assert data["location"] == "Seattle, WA"
    assert data["headline"] == "Staff Engineer"


@pytest.mark.asyncio
async def test_candidate_profile_ownership_isolation(client: AsyncClient):
    """Test user can only access their own profile and cannot view another's."""
    token1, _ = await create_user_and_token(client, "user1@example.com", "User One")
    token2, _ = await create_user_and_token(client, "user2@example.com", "User Two")

    await client.post(
        "/api/v1/candidates/me/profile",
        json={"headline": "User 1 Headline"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    # User 2 accesses their own profile -> 404 (not User 1's)
    res = await client.get(
        "/api/v1/candidates/me/profile",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res.status_code == 404
