from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="TalentLens AI Recruitment & Career Intelligence Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["system"])
def root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "online",
        "version": "0.1.0",
        "docs": f"{settings.API_V1_STR}/docs",
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
