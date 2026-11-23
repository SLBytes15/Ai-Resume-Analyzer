from fastapi import APIRouter
from app.api.v1.applications import router as candidate_applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.candidates import router as candidate_router
from app.api.v1.jobs import router as recruiter_jobs_router
from app.api.v1.organizations import router as org_router
from app.api.v1.public_jobs import router as public_jobs_router
from app.api.v1.recruiter_applications import router as recruiter_applications_router
from app.api.v1.resume_analysis import router as resume_analysis_router
from app.api.v1.resumes import router as resume_router
from app.api.v1.screenings import router as screenings_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(org_router, prefix="/recruiter/organizations", tags=["recruiter-organizations"])
api_router.include_router(candidate_router, prefix="/candidates", tags=["candidates"])
api_router.include_router(resume_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(recruiter_jobs_router, prefix="/organizations/{organization_id}/jobs", tags=["recruiter-jobs"])
api_router.include_router(recruiter_jobs_router, prefix="/recruiter/organizations/{organization_id}/jobs", tags=["recruiter-jobs"])
api_router.include_router(public_jobs_router, prefix="/jobs", tags=["public-jobs"])
# Milestone 5: Application routes
api_router.include_router(candidate_applications_router, tags=["candidate-applications"])
api_router.include_router(recruiter_applications_router, prefix="/organizations", tags=["recruiter-applications"])
api_router.include_router(recruiter_applications_router, prefix="/recruiter/organizations", tags=["recruiter-applications"])
# Milestone 6: AI-Powered Candidate Screening Engine routes
api_router.include_router(screenings_router, prefix="/organizations", tags=["screenings"])
api_router.include_router(screenings_router, prefix="/recruiter/organizations", tags=["screenings"])
# Milestone 7: Candidate Resume Intelligence & Career Guidance routes
api_router.include_router(resume_analysis_router, tags=["resume-analysis"])
