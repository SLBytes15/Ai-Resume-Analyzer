from fastapi import FastAPI as ft
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.batch_matcher import run_candidate_matcher

app = ft()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobDescription(BaseModel):
    jd_id: str
    role: str
    skills: list[str]
    minimum_years: int


@app.get("/")
def home():
    return {"message": "Ai Recruiter Assistant API"}


@app.post("/match")
def match(jd: JobDescription):
    try:
        jd_dict = jd.model_dump()
        candidate_profiles_dir = "./candidate_profiles"
        chroma_db_path = "./chroma_db"

        results = run_candidate_matcher(
            jd_data=jd_dict,
            profiles_dir=candidate_profiles_dir,
            chroma_db_path=chroma_db_path,
        )

        return {"status": "success", "total_matches": len(results), "candidate": results}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc), "candidate": []})

