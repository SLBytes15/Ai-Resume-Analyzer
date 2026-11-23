import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models import (
    Application,
    ApplicationStatusHistory,
    Base,
    CandidateProfile,
    Job,
    Organization,
    OrganizationMembership,
    Resume,
    ResumeAnalysis,
    ScreeningInsight,
    CareerConversation,
    CareerMessage,
    ScreeningResult,
    ScreeningRun,
    User,
)
from app.services.storage_service import storage_service


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated clean database session using NullPool for each test."""
    test_engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    async_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Ensure schema exists and clean up tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE career_messages, career_conversations, resume_analyses, screening_insights, screening_results, screening_runs, application_status_history, applications, jobs, resumes, candidate_profiles, organization_memberships, organizations, users RESTART IDENTITY CASCADE;"
            )
        )
        await session.commit()
        try:
            yield session
        finally:
            await session.close()

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide AsyncClient with get_db overridden to use the per-test database session."""
    # Use isolated temp dir for file storage during test
    temp_dir = tempfile.mkdtemp(prefix="talentlens_test_resumes_")
    orig_base_dir = storage_service.base_dir
    storage_service.base_dir = Path(temp_dir).resolve()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
    storage_service.base_dir = orig_base_dir
    shutil.rmtree(temp_dir, ignore_errors=True)
