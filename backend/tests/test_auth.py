from datetime import timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token, verify_password
from app.models.user import User


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, db_session: AsyncSession):
    """Test successful user registration returns 201, token, and safe user data."""
    payload = {
        "email": "candidate@example.com",
        "password": "SecurePassword123!",
        "full_name": "Jane Candidate",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data

    user = data["user"]
    assert user["email"] == "candidate@example.com"
    assert user["full_name"] == "Jane Candidate"
    assert user["is_active"] is True
    assert "id" in user
    assert "password_hash" not in user
    assert "password" not in user

    # Verify user in database
    result = await db_session.execute(
        select(User).where(User.email == "candidate@example.com")
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.password_hash != "SecurePassword123!"
    assert verify_password("SecurePassword123!", db_user.password_hash)


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registering with an existing email returns 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123!",
        "full_name": "First User",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt to register again with same email (different casing)
    res2 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "DUPLICATE@example.com",
            "password": "AnotherPassword456!",
            "full_name": "Second User",
        },
    )
    assert res2.status_code == 409
    assert res2.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Test registration fails with 422 on invalid email format."""
    payload = {
        "email": "not-a-valid-email",
        "password": "SecurePassword123!",
        "full_name": "Jane Candidate",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Test registration fails with 422 if password is less than 8 characters."""
    payload = {
        "email": "shortpass@example.com",
        "password": "short",
        "full_name": "Short Pass User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test login with valid credentials returns 200 and access token."""
    # First register user
    reg_payload = {
        "email": "loginuser@example.com",
        "password": "Password789!",
        "full_name": "Login User",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "loginuser@example.com",
        "password": "Password789!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "loginuser@example.com"
    assert "password_hash" not in data["user"]


@pytest.mark.asyncio
async def test_login_case_insensitive_email(client: AsyncClient):
    """Test login works regardless of email case."""
    reg_payload = {
        "email": "case.sensitive@example.com",
        "password": "Password789!",
        "full_name": "Case User",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login with uppercase email
    login_payload = {
        "email": "CASE.SENSITIVE@EXAMPLE.COM",
        "password": "Password789!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "case.sensitive@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with incorrect password returns 401 Unauthorized."""
    reg_payload = {
        "email": "wrongpass@example.com",
        "password": "CorrectPassword123!",
        "full_name": "Wrong Pass User",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpass@example.com",
        "password": "IncorrectPassword999!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """Test login with non-existent email returns 401 Unauthorized."""
    login_payload = {
        "email": "nobody@example.com",
        "password": "SomePassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    """Test inactive user cannot log in and receives 401 Unauthorized."""
    reg_payload = {
        "email": "inactive@example.com",
        "password": "Password123!",
        "full_name": "Inactive User",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    user_id = reg_res.json()["user"]["id"]

    # Deactivate user in database
    result = await db_session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    user.is_active = False
    await db_session.commit()

    # Attempt login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 401
    assert login_res.json()["detail"] == "Inactive user account"


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient):
    """Test /api/v1/auth/me returns current user profile with valid Bearer token."""
    reg_payload = {
        "email": "me.test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Me Tester",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    user_data = response.json()
    assert user_data["email"] == "me.test@example.com"
    assert user_data["full_name"] == "Me Tester"
    assert user_data["is_active"] is True
    assert "password_hash" not in user_data


@pytest.mark.asyncio
async def test_get_me_unauthorized_without_token(client: AsyncClient):
    """Test /api/v1/auth/me returns 401/403 when Authorization header is missing."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """Test /api/v1/auth/me returns 401 with a malformed or forged token."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer forged-or-malformed-token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_me_expired_token(client: AsyncClient):
    """Test /api/v1/auth/me returns 401 with an expired token."""
    reg_payload = {
        "email": "expired@example.com",
        "password": "SecurePassword123!",
        "full_name": "Expired User",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    user_id = reg_res.json()["user"]["id"]

    # Create expired token (-10 minutes)
    expired_token = create_access_token(
        subject=str(user_id),
        expires_delta=timedelta(minutes=-10),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_users_table_isolation_contract(db_session: AsyncSession):
    """Verify Users model has NO organization_id and NO hardcoded role columns."""
    column_names = [c.name for c in User.__table__.columns]
    assert "organization_id" not in column_names, "users table must NOT contain organization_id"
    assert "role" not in column_names, "users table must NOT contain hardcoded role column"
    assert "is_recruiter" not in column_names
    assert "is_candidate" not in column_names
    assert "email" in column_names
    assert "password_hash" in column_names
    assert "full_name" in column_names
    assert "is_active" in column_names
