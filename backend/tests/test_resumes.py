import io
import uuid
from unittest.mock import AsyncMock, patch
import fitz
import pytest
from httpx import AsyncClient
from app.schemas.resume import ParsedResumeData


def make_pdf_bytes(text: str = "Alex Smith\nSoftware Engineer\nSkills: Python, React, PostgreSQL") -> bytes:
    """Helper creating valid in-memory PDF bytes with text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def make_scanned_pdf_bytes() -> bytes:
    """Helper creating valid PDF bytes with NO text (empty page)."""
    doc = fitz.open()
    doc.new_page()  # Blank page
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


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


@pytest.fixture
def mock_ollama_success():
    """Mock LLMParser returning valid ParsedResumeData."""
    mock_data = ParsedResumeData(
        full_name="Alex Smith",
        email="alex@example.com",
        phone="+1-555-0100",
        professional_summary="Senior Engineer with 5 years experience.",
        skills=["Python", "FastAPI", "PostgreSQL", "React"],
        education=[
            {
                "institution": "University of Tech",
                "degree": "B.S.",
                "field_of_study": "Computer Science",
                "start_date": "2018",
                "end_date": "2022",
            }
        ],
        experience=[
            {
                "company": "Tech Corp",
                "job_title": "Backend Developer",
                "description": "Built scalable APIs in FastAPI.",
                "start_date": "2022",
                "end_date": "Present",
            }
        ],
        projects=[],
        certifications=["AWS Certified Developer"],
    )
    with patch(
        "app.services.resume_service.llm_parser.parse_resume",
        new=AsyncMock(return_value=mock_data),
    ) as mock:
        yield mock


@pytest.mark.asyncio
async def test_upload_resume_success(client: AsyncClient, mock_ollama_success):
    """Test valid PDF upload extracts text, parses structured data, and marks resume active."""
    token, _ = await create_user_and_token(client, "uploader@example.com", "Uploader User")
    pdf_content = make_pdf_bytes("Jane Doe\nFull Stack Developer\nSkills: Python, TypeScript")

    files = {"file": ("jane_resume.pdf", pdf_content, "application/pdf")}
    res = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["original_filename"] == "jane_resume.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["file_size"] == len(pdf_content)
    assert data["parsing_status"] == "COMPLETED"
    assert data["is_active"] is True  # First resume is automatically active
    assert "Jane Doe" in data["extracted_text"]
    assert data["parsed_data"]["full_name"] == "Alex Smith"
    assert "Python" in data["parsed_data"]["skills"]


@pytest.mark.asyncio
async def test_upload_invalid_extension(client: AsyncClient):
    """Test uploading non-PDF extension fails with 400."""
    token, _ = await create_user_and_token(client, "txt@example.com", "Txt User")
    files = {"file": ("resume.txt", b"Plain text content", "text/plain")}

    res = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "Only PDF documents" in res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_invalid_magic_bytes(client: AsyncClient):
    """Test uploading a fake PDF (missing %PDF- header) fails with 400."""
    token, _ = await create_user_and_token(client, "fake@example.com", "Fake PDF User")
    files = {"file": ("corrupt.pdf", b"This is not a real PDF file header", "application/pdf")}

    res = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "Missing %PDF-" in res.json()["detail"]


@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient):
    """Test uploading 0-byte file fails with 400."""
    token, _ = await create_user_and_token(client, "empty@example.com", "Empty User")
    files = {"file": ("empty.pdf", b"", "application/pdf")}

    res = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_oversized_file(client: AsyncClient):
    """Test uploading file > 5MB fails with 413."""
    token, _ = await create_user_and_token(client, "large@example.com", "Large File User")
    # 5MB + 10 bytes
    large_bytes = b"%PDF-1.4\n" + b"x" * (5 * 1024 * 1024 + 10)
    files = {"file": ("large.pdf", large_bytes, "application/pdf")}

    res = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 413
    assert "exceeds maximum allowed upload size" in res.json()["detail"]


@pytest.mark.asyncio
async def test_scanned_pdf_without_text_marks_failed_status(client: AsyncClient):
    """Test PDF without extractable text sets parsing_status to FAILED but preserves file."""
    token, _ = await create_user_and_token(client, "scanned@example.com", "Scanned User")
    pdf_content = make_scanned_pdf_bytes()

    files = {"file": ("scanned.pdf", pdf_content, "application/pdf")}
    res = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["parsing_status"] == "FAILED"
    assert "No extractable text found" in data["parsing_error"]
    assert data["extracted_text"] is None


@pytest.mark.asyncio
async def test_ai_extraction_failure_preserves_extracted_text(client: AsyncClient):
    """Test that when Ollama fails, extracted_text and original file are preserved and status is FAILED."""
    token, _ = await create_user_and_token(client, "llm_fail@example.com", "LLM Fail User")
    pdf_content = make_pdf_bytes("John Candidate\nDevOps Engineer\nKubernetes, Docker")

    with patch(
        "app.services.resume_service.llm_parser.parse_resume",
        new=AsyncMock(side_effect=Exception("Ollama connection timeout")),
    ):
        files = {"file": ("devops.pdf", pdf_content, "application/pdf")}
        res = await client.post(
            "/api/v1/resumes/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["parsing_status"] == "FAILED"
        assert "Ollama connection timeout" in data["parsing_error"]
        assert "DevOps Engineer" in data["extracted_text"]  # Text is preserved!


@pytest.mark.asyncio
async def test_multiple_resume_versions_and_single_active_invariant(client: AsyncClient, mock_ollama_success):
    """Test uploading multiple versions and switching active resume."""
    token, _ = await create_user_and_token(client, "multiversion@example.com", "Multi User")

    pdf1 = make_pdf_bytes("Version 1 Text")
    pdf2 = make_pdf_bytes("Version 2 Text")

    # Upload version 1
    res1 = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("v1.pdf", pdf1, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    v1_id = res1.json()["id"]
    assert res1.json()["is_active"] is True

    # Upload version 2
    res2 = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("v2.pdf", pdf2, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    v2_id = res2.json()["id"]
    assert res2.json()["is_active"] is False  # Second resume is not active by default

    # List resumes -> both exist
    list_res = await client.get(
        "/api/v1/resumes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(list_res.json()) == 2

    # Switch active resume to version 2
    active_res = await client.patch(
        f"/api/v1/resumes/{v2_id}/active",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert active_res.status_code == 200
    assert active_res.json()["is_active"] is True

    # Verify version 1 was deactivated
    get_v1 = await client.get(
        f"/api/v1/resumes/{v1_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_v1.json()["is_active"] is False


@pytest.mark.asyncio
async def test_resume_ownership_isolation(client: AsyncClient, mock_ollama_success):
    """Test candidate cannot access, download, or delete another candidate's resume."""
    token1, _ = await create_user_and_token(client, "c1@example.com", "Candidate One")
    token2, _ = await create_user_and_token(client, "c2@example.com", "Candidate Two")

    pdf = make_pdf_bytes("Candidate One Private Resume")
    res1 = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("c1_resume.pdf", pdf, "application/pdf")},
        headers={"Authorization": f"Bearer {token1}"},
    )
    c1_resume_id = res1.json()["id"]

    # Candidate Two attempts to view C1's resume -> 404
    res_view = await client.get(
        f"/api/v1/resumes/{c1_resume_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res_view.status_code == 404

    # Candidate Two attempts to download C1's resume -> 404
    res_dl = await client.get(
        f"/api/v1/resumes/{c1_resume_id}/download",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res_dl.status_code == 404

    # Candidate Two attempts to delete C1's resume -> 404
    res_del = await client.delete(
        f"/api/v1/resumes/{c1_resume_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert res_del.status_code == 404

    # Candidate Two's resume list is empty
    res_list = await client.get(
        "/api/v1/resumes",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert len(res_list.json()) == 0


@pytest.mark.asyncio
async def test_resume_download_and_deletion(client: AsyncClient, mock_ollama_success):
    """Test downloading and deleting a resume."""
    token, _ = await create_user_and_token(client, "dl@example.com", "DL User")
    pdf_content = make_pdf_bytes("Original Resume Content To Download")

    upload_res = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("original.pdf", pdf_content, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    resume_id = upload_res.json()["id"]

    # Download
    dl_res = await client.get(
        f"/api/v1/resumes/{resume_id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dl_res.status_code == 200
    assert dl_res.content == pdf_content
    assert dl_res.headers["content-type"] == "application/pdf"

    # Delete
    del_res = await client.delete(
        f"/api/v1/resumes/{resume_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200

    # Verify deleted
    get_res = await client.get(
        f"/api/v1/resumes/{resume_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_llm_parser_fallback_behavior():
    """Test LLM parser falls back to secondary model if primary model fails."""
    from app.services.llm_parser import LLMParser, LLMParserError

    parser = LLMParser(primary_model="qwen3:4b", fallback_model="llama3.2:1b")

    call_history = []

    async def fake_query(client, model, text):
        call_history.append(model)
        if model == "qwen3:4b":
            raise Exception("Primary model out of memory")
        return '{"full_name": "Fallback User", "skills": ["Go", "Kubernetes"]}'

    with patch.object(parser, "_query_ollama", side_effect=fake_query):
        result = await parser.parse_resume("Resume content here")
        assert result.full_name == "Fallback User"
        assert result.skills == ["Go", "Kubernetes"]
        assert call_history == ["qwen3:4b", "llama3.2:1b"]


@pytest.mark.asyncio
async def test_llm_parser_all_models_fail():
    """Test LLM parser raises LLMParserError when both models fail."""
    from app.services.llm_parser import LLMParser, LLMParserError

    parser = LLMParser(primary_model="qwen3:4b", fallback_model="llama3.2:1b")

    async def fake_query(client, model, text):
        raise Exception(f"Model {model} unavailable")

    with patch.object(parser, "_query_ollama", side_effect=fake_query):
        with pytest.raises(LLMParserError) as exc_info:
            await parser.parse_resume("Resume text")
        assert "All LLM extraction attempts failed" in str(exc_info.value)
