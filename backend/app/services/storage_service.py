import hashlib
import os
from pathlib import Path
import uuid
from typing import Tuple
from fastapi import HTTPException, status
from app.core.config import settings


class StorageServiceError(Exception):
    pass


class StorageService:
    def __init__(self, base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_pdf_content(self, content: bytes, original_filename: str) -> None:
        """Validate PDF file size, extension, and magic bytes."""
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File exceeds maximum allowed upload size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB",
            )

        # Check extension
        if not original_filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF documents (.pdf) are supported",
            )

        # Check magic bytes: PDF header must begin with %PDF-
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF structure: Missing %PDF- header magic bytes",
            )

    def calculate_sha256(self, content: bytes) -> str:
        """Calculate SHA-256 hex digest of file content."""
        return hashlib.sha256(content).hexdigest()

    def get_relative_storage_path(self, candidate_id: uuid.UUID, resume_id: uuid.UUID) -> str:
        """Return relative storage path (e.g., '{candidate_id}/{resume_id}.pdf')."""
        return f"{candidate_id}/{resume_id}.pdf"

    def get_absolute_path(self, relative_path: str) -> Path:
        """Resolve relative path to secure absolute path, preventing path traversal."""
        clean_path = Path(relative_path).as_posix().lstrip("/")
        base_resolved = self.base_dir.resolve()
        resolved = (base_resolved / clean_path).resolve()

        try:
            if not resolved.is_relative_to(base_resolved):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid file path access detected",
                )
        except AttributeError:  # Fallback for python < 3.9 if ever needed
            if not str(resolved).startswith(str(base_resolved)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid file path access detected",
                )
        return resolved

    def save_file(
        self, candidate_id: uuid.UUID, resume_id: uuid.UUID, content: bytes
    ) -> str:
        """Save file bytes securely to local storage directory. Returns relative storage path."""
        rel_path = self.get_relative_storage_path(candidate_id, resume_id)
        abs_path = self.get_absolute_path(rel_path)

        abs_path.parent.mkdir(parents=True, exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(content)

        return rel_path

    def delete_file(self, relative_path: str) -> bool:
        """Delete stored file if it exists."""
        try:
            abs_path = self.get_absolute_path(relative_path)
            if abs_path.exists():
                abs_path.unlink()
                # Clean up empty parent directory if empty
                try:
                    if abs_path.parent != self.base_dir and not any(abs_path.parent.iterdir()):
                        abs_path.parent.rmdir()
                except Exception:
                    pass
                return True
        except Exception:
            pass
        return False


storage_service = StorageService()
