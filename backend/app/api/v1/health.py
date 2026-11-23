from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/live", summary="Process liveness check")
async def liveness():
    """Liveness probe: verifies the web server process is actively handling requests."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready", summary="Service readiness check")
async def readiness(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe:
    - Tests PostgreSQL database connectivity (SELECT 1). Fails with 503 if DB is down.
    - Probes Ollama reachability without failing core readiness if Ollama is degraded.
    """
    db_connected = False
    ai_status = "unavailable"
    errors = []

    # 1. Database check
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        errors.append(f"Database error: {str(e)}")

    # 2. Ollama check (non-fatal)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ai_status = "available"
            else:
                ai_status = f"unhealthy (HTTP {resp.status_code})"
    except Exception:
        ai_status = "offline"

    payload = {
        "status": "ready" if db_connected else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_connected else "disconnected",
        "ai_service": ai_status,
    }

    if not db_connected:
        payload["errors"] = errors
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload
        )

    return payload
