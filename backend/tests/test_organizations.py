import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token
from app.models.organization import Organization, OrganizationMembership, OrganizationRole
from app.models.user import User


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
async def test_create_organization_creator_becomes_owner(client: AsyncClient):
    """Test creating an organization atomically sets the creator as OWNER."""
    token, user = await create_user_and_token(client, "owner@acme.com", "Acme Owner")

    payload = {"name": "Acme Innovations", "slug": "acme-innovations"}
    res = await client.post(
        "/api/v1/recruiter/organizations",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    org_data = res.json()
    assert org_data["name"] == "Acme Innovations"
    assert org_data["slug"] == "acme-innovations"
    assert org_data["role"] == "OWNER"
    assert "id" in org_data


@pytest.mark.asyncio
async def test_create_organization_auto_generates_slug(client: AsyncClient):
    """Test creating an organization without slug automatically generates a slug."""
    token, user = await create_user_and_token(client, "slug@acme.com", "Slug Creator")

    payload = {"name": "Global Tech Ventures!"}
    res = await client.post(
        "/api/v1/recruiter/organizations",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["slug"] == "global-tech-ventures"


@pytest.mark.asyncio
async def test_create_organization_duplicate_slug_rejected(client: AsyncClient):
    """Test duplicate slug returns 409 Conflict."""
    token1, _ = await create_user_and_token(client, "u1@org.com", "User One")
    token2, _ = await create_user_and_token(client, "u2@org.com", "User Two")

    payload = {"name": "Stark Industries", "slug": "stark-industries"}
    res1 = await client.post(
        "/api/v1/recruiter/organizations",
        json=payload,
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res1.status_code == 201

    res2 = await client.post(
        "/api/v1/recruiter/organizations",
        json=payload,
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res2.status_code == 409
    assert "already taken" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_list_user_organizations(client: AsyncClient):
    """Test listing user organizations returns organizations with the user's role."""
    token, _ = await create_user_and_token(client, "multiorg@acme.com", "Multi Org")

    # Create two organizations
    await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Org Alpha", "slug": "org-alpha"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Org Beta", "slug": "org-beta"},
        headers={"Authorization": f"Bearer {token}"},
    )

    res = await client.get(
        "/api/v1/recruiter/organizations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    orgs = res.json()
    assert len(orgs) == 2
    assert {o["slug"] for o in orgs} == {"org-alpha", "org-beta"}
    assert all(o["role"] == "OWNER" for o in orgs)


@pytest.mark.asyncio
async def test_add_member_by_owner_success(client: AsyncClient):
    """Test OWNER can add a new member by email with RECRUITER role."""
    owner_token, _ = await create_user_and_token(client, "boss@acme.com", "Boss User")
    _, rec_user = await create_user_and_token(client, "recruiter@acme.com", "Recruiter Joe")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Recruitment Firm", "slug": "rec-firm"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    add_res = await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "recruiter@acme.com", "role": "RECRUITER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert add_res.status_code == 201, add_res.text
    data = add_res.json()
    assert data["email"] == "recruiter@acme.com"
    assert data["role"] == "RECRUITER"
    assert data["user_id"] == rec_user["id"]


@pytest.mark.asyncio
async def test_add_member_nonexistent_email(client: AsyncClient):
    """Test adding an unregistered email returns 404."""
    owner_token, _ = await create_user_and_token(client, "owner404@acme.com", "Owner")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Org 404", "slug": "org-404"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    res = await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "does.not.exist@nowhere.com", "role": "RECRUITER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 404
    assert "does not exist on the platform" in res.json()["detail"]


@pytest.mark.asyncio
async def test_add_member_duplicate_membership(client: AsyncClient):
    """Test adding an existing member returns 409 Conflict."""
    owner_token, _ = await create_user_and_token(client, "dup.owner@acme.com", "Owner")
    _, member = await create_user_and_token(client, "dup.member@acme.com", "Member")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Dup Org", "slug": "dup-org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    # First add
    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "dup.member@acme.com", "role": "VIEWER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Second add attempt
    res2 = await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "dup.member@acme.com", "role": "RECRUITER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res2.status_code == 409
    assert "already a member" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_add_member_permission_denied_for_recruiter(client: AsyncClient):
    """Test RECRUITER or VIEWER cannot add members."""
    owner_token, _ = await create_user_and_token(client, "pow.owner@acme.com", "Owner")
    rec_token, _ = await create_user_and_token(client, "pow.rec@acme.com", "Recruiter")
    _, target = await create_user_and_token(client, "pow.target@acme.com", "Target")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Perm Org", "slug": "perm-org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    # Add rec user as RECRUITER
    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "pow.rec@acme.com", "role": "RECRUITER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Recruiter attempts to add target
    res = await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "pow.target@acme.com", "role": "VIEWER"},
        headers={"Authorization": f"Bearer {rec_token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_cannot_add_member_directly_as_owner(client: AsyncClient):
    """Test cannot assign OWNER directly during member add."""
    owner_token, _ = await create_user_and_token(client, "direct.owner@acme.com", "Owner")
    await create_user_and_token(client, "second.owner@acme.com", "Second")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Single Owner Org", "slug": "single-owner-org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    res = await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "second.owner@acme.com", "role": "OWNER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 400
    assert "only one OWNER" in res.json()["detail"]


@pytest.mark.asyncio
async def test_list_members(client: AsyncClient):
    """Test listing members returns all active members with user profiles."""
    owner_token, _ = await create_user_and_token(client, "list.owner@acme.com", "List Owner")
    await create_user_and_token(client, "list.m1@acme.com", "List Member 1")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "List Members Org", "slug": "list-members-org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "list.m1@acme.com", "role": "RECRUITER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    members_res = await client.get(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) == 2
    roles = {m["role"] for m in members}
    assert roles == {"OWNER", "RECRUITER"}


@pytest.mark.asyncio
async def test_prevent_demotion_of_owner(client: AsyncClient):
    """Test attempting to demote the OWNER directly fails."""
    owner_token, owner_user = await create_user_and_token(
        client, "demote.owner@acme.com", "Demote Owner"
    )

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Demote Org", "slug": "demote-org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    # Attempt to demote owner to ADMIN
    res = await client.put(
        f"/api/v1/recruiter/organizations/{org_id}/members/{owner_user['id']}",
        json={"role": "ADMIN"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 400
    assert "Cannot demote the active organization OWNER" in res.json()["detail"]


@pytest.mark.asyncio
async def test_prevent_removal_of_owner(client: AsyncClient):
    """Test attempting to remove the OWNER fails."""
    owner_token, owner_user = await create_user_and_token(
        client, "remove.owner@acme.com", "Remove Owner"
    )

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Remove Org", "slug": "remove-org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    # Attempt to remove owner
    res = await client.delete(
        f"/api/v1/recruiter/organizations/{org_id}/members/{owner_user['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 400
    assert "Cannot remove the organization OWNER" in res.json()["detail"]


@pytest.mark.asyncio
async def test_ownership_transfer_atomically_maintains_single_owner(client: AsyncClient):
    """Test transferring ownership makes target OWNER and demotes old owner to ADMIN."""
    owner_token, owner_user = await create_user_and_token(
        client, "old.owner@acme.com", "Old Owner"
    )
    _, new_user = await create_user_and_token(client, "new.owner@acme.com", "New Owner")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Transfer Org", "slug": "transfer-org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    # Add new user as ADMIN
    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "new.owner@acme.com", "role": "ADMIN"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Transfer ownership
    transfer_res = await client.put(
        f"/api/v1/recruiter/organizations/{org_id}/members/{new_user['id']}",
        json={"role": "OWNER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert transfer_res.status_code == 200
    assert transfer_res.json()["role"] == "OWNER"

    # Verify members
    members_res = await client.get(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    members = members_res.json()
    role_map = {m["user_id"]: m["role"] for m in members}
    assert role_map[owner_user["id"]] == "ADMIN"
    assert role_map[new_user["id"]] == "OWNER"


@pytest.mark.asyncio
async def test_remove_member_success(client: AsyncClient):
    """Test removing a regular member succeeds."""
    owner_token, _ = await create_user_and_token(client, "rm.owner@acme.com", "RM Owner")
    _, target_user = await create_user_and_token(client, "rm.target@acme.com", "Target")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "RM Org", "slug": "rm-org"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_res.json()["id"]

    await client.post(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        json={"email": "rm.target@acme.com", "role": "RECRUITER"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    rm_res = await client.delete(
        f"/api/v1/recruiter/organizations/{org_id}/members/{target_user['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert rm_res.status_code == 200

    # Verify target is no longer in member list
    members_res = await client.get(
        f"/api/v1/recruiter/organizations/{org_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    member_ids = [m["user_id"] for m in members_res.json()]
    assert target_user["id"] not in member_ids


@pytest.mark.asyncio
async def test_switch_organization_context_success(client: AsyncClient):
    """Test switching organization issues a new JWT carrying active_org_id and org_role."""
    token, _ = await create_user_and_token(client, "switch.user@acme.com", "Switch User")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Context Org", "slug": "context-org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    org_id = org_res.json()["id"]

    switch_res = await client.post(
        "/api/v1/auth/switch-organization",
        json={"organization_id": org_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert switch_res.status_code == 200, switch_res.text
    switch_data = switch_res.json()

    assert switch_data["active_org_id"] == org_id
    assert switch_data["org_name"] == "Context Org"
    assert switch_data["org_role"] == "OWNER"
    assert "access_token" in switch_data

    # Decode and verify JWT claims
    claims = decode_access_token(switch_data["access_token"])
    assert claims["active_org_id"] == org_id
    assert claims["org_role"] == "OWNER"


@pytest.mark.asyncio
async def test_switch_organization_unauthorized_org(client: AsyncClient):
    """Test switching to an organization where user is not a member returns 403."""
    user1_token, _ = await create_user_and_token(client, "u1.ctx@acme.com", "U1")
    user2_token, _ = await create_user_and_token(client, "u2.ctx@acme.com", "U2")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Private Org", "slug": "private-org"},
        headers={"Authorization": f"Bearer {user1_token}"},
    )
    org_id = org_res.json()["id"]

    # User 2 attempts to switch to User 1's org
    switch_res = await client.post(
        "/api/v1/auth/switch-organization",
        json={"organization_id": org_id},
        headers={"Authorization": f"Bearer {user2_token}"},
    )
    assert switch_res.status_code == 403
    assert "Not an active member" in switch_res.json()["detail"]


@pytest.mark.asyncio
async def test_database_constraints_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verify unique constraints and foreign key cascade on organizations & memberships."""
    token, user = await create_user_and_token(client, "db.test@acme.com", "DB Tester")

    org_res = await client.post(
        "/api/v1/recruiter/organizations",
        json={"name": "Cascade Org", "slug": "cascade-org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    org_id = uuid.UUID(org_res.json()["id"])
    user_id = uuid.UUID(user["id"])

    # Verify membership exists in DB
    membership = (
        await db_session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == org_id,
                OrganizationMembership.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    assert membership is not None
    assert membership.role == "OWNER"

    # Delete organization and check cascade delete on memberships
    org = (
        await db_session.execute(select(Organization).where(Organization.id == org_id))
    ).scalar_one()
    await db_session.delete(org)
    await db_session.commit()

    # Membership should be gone
    membership_after = (
        await db_session.execute(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == org_id
            )
        )
    ).scalar_one_or_none()
    assert membership_after is None
