import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import request_id_ctx, setup_logging

logger = logging.getLogger(__name__)

# Configure API Documentation conditionally based on environment settings
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="TalentLens AI Recruitment & Career Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DOCS_ENABLED else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DOCS_ENABLED else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DOCS_ENABLED else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    HTTP Middleware:
    - Generates or adopts X-Request-ID for distributed request tracing.
    - Tracks request latency.
    - Emits structured access log.
    - Catches unhandled exceptions and returns standardized error envelope without stack trace leak.
    """
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_ctx.set(req_id)
    start_time = time.time()
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        logger.info(
            f"{request.method} {request.url.path} completed with {response.status_code} in {duration_ms}ms"
        )
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.exception(
            f"Unhandled exception during {request.method} {request.url.path} after {duration_ms}ms: {exc}"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": req_id},
            headers={"X-Request-ID": req_id},
        )
    finally:
        request_id_ctx.reset(token)


@app.on_event("startup")
def startup_event():
    """Application startup initialization and security validation."""
    setup_logging()
    settings.validate_production_settings()


# Include v1 API router & Health routers
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(health_router, prefix=f"{settings.API_V1_STR}/health", tags=["health"])
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["system"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "online",
        "version": "0.1.0",
        "docs": f"{settings.API_V1_STR}/docs" if settings.DOCS_ENABLED else "disabled",
    }


@app.get("/health", tags=["system"])
@app.get(f"{settings.API_V1_STR}/health", tags=["system"])
def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


# Legacy compatibility for existing batch matcher
class JobDescription(BaseModel):
    raw_text: str


@app.post("/match", tags=["legacy"])
def match(jd: JobDescription):
    try:
        from services.batch_matcher import run_candidate_matcher

        candidate_profiles_dir = "./candidate_profiles"
        chroma_db_path = "./chroma_db"

        results = run_candidate_matcher(
            raw_text=jd.raw_text,
            profiles_dir=candidate_profiles_dir,
            chroma_db_path=chroma_db_path,
        )

        return {"status": "success", "total_matches": len(results), "candidate": results}
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc), "candidate": []},
        )
