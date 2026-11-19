# TalentLens MVP: RESTful API Specification Plan

**Document Version**: 1.0  
**API Standard**: FastAPI / OpenAPI 3.1  
**Base URL**: `/api/v1`  
**Authentication**: Bearer JWT (`Authorization: Bearer <token>`)  

---

## 1. Authentication & Context Architecture

### 1.1 Context-Aware JWT Payload
TalentLens MVP uses JWT tokens encoding user identity and active tenant context:
```json
{
  "sub": "b2f679dc-8a21-4f3b-8219-c43e74a81b29",
  "email": "recruiter@acme.com",
  "system_role": "PLATFORM_USER",
  "active_org_id": "c1f3d3b7-7e62-4ef8-a401-44755e347aa9",
  "org_role": "RECRUITER",
  "exp": 1720000900
}
```

### 1.2 Authorization Guards (FastAPI Dependencies)
- `get_current_user`: Decodes JWT, validates user exists and is active.
- `require_candidate`: Asserts the user is acting as an independent candidate.
- `get_active_recruiter_context`:
  1. Verifies `active_org_id` is present in token.
  2. Queries `organization_memberships` ensuring the user has an active membership in `active_org_id`.
  3. Returns `RecruiterContext(user=..., organization_id=..., role=...)`.

---

## 2. API Endpoint Matrix

| Domain | Method | Path | Required Role / Context | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/auth/register` | Public | Register new candidate or recruiter |
| **Auth** | `POST` | `/auth/login` | Public | Authenticate user, return JWT |
| **Auth** | `POST` | `/auth/switch-organization` | Authenticated Recruiter | Switch active organization context & return new JWT |
| **Auth** | `GET` | `/auth/me` | Authenticated | Get current user identity & organization memberships |
| **Candidate** | `GET` | `/candidate/profile` | Candidate | Retrieve candidate personal profile |
| **Candidate** | `PUT` | `/candidate/profile` | Candidate | Update candidate headline, skills, and experience |
| **Candidate** | `POST` | `/candidate/resumes/upload` | Candidate | Upload PDF resume, extract text, parse via Ollama |
| **Candidate** | `GET` | `/candidate/resumes` | Candidate | List all uploaded resume versions |
| **Candidate** | `GET` | `/candidate/resumes/{id}` | Candidate | View parsed resume details and extracted skills |
| **Jobs (Public)**| `GET` | `/jobs` | Public / Candidate | Search & list published job openings across organizations |
| **Jobs (Public)**| `GET` | `/jobs/{id}` | Public / Candidate | View published job requisition requirements |
| **Applications** | `POST` | `/candidate/jobs/{id}/apply` | Candidate | Apply to job with specific `resume_id` (Idempotent) |
| **Applications** | `GET` | `/candidate/applications` | Candidate | List candidate's submitted applications with status |
| **Recruiter Org**| `POST` | `/recruiter/organizations` | Authenticated User | Create a new organization (User becomes `OWNER`) |
| **Recruiter Org**| `GET` | `/recruiter/organizations` | Authenticated User | List organizations user belongs to |
| **Recruiter Org**| `POST` | `/recruiter/organizations/{id}/members` | Recruiter (`ADMIN`+) | Add a user to organization with specified role |
| **Recruiter Org**| `GET` | `/recruiter/organizations/{id}/members` | Recruiter (`VIEWER`+) | List members of active organization |
| **Recruiter Jobs**| `POST` | `/recruiter/jobs` | Recruiter (`RECRUITER`+) | Create job requisition with structured requirements |
| **Recruiter Jobs**| `GET` | `/recruiter/jobs` | Recruiter (`VIEWER`+) | List active organization's jobs |
| **Recruiter Jobs**| `GET` | `/recruiter/jobs/{id}` | Recruiter (`VIEWER`+) | View detailed job requisition |
| **Recruiter Jobs**| `PUT` | `/recruiter/jobs/{id}` | Recruiter (`RECRUITER`+) | Update job details, publish, or close requisition |
| **Recruiter Apps**| `GET` | `/recruiter/jobs/{id}/applications` | Recruiter (`VIEWER`+) | List applicants for this requisition |
| **Recruiter Apps**| `GET` | `/recruiter/applications/{id}/resume` | Recruiter (`VIEWER`+) | Download/view submitted resume PDF |
| **Recruiter Apps**| `PUT` | `/recruiter/applications/{id}/status` | Recruiter (`RECRUITER`+) | Manually update candidate status |
| **AI Screening** | `POST` | `/recruiter/jobs/{id}/screen` | Recruiter (`RECRUITER`+) | Trigger deterministic AI screening on applicants |
| **AI Screening** | `GET` | `/recruiter/jobs/{id}/screening-results`| Recruiter (`VIEWER`+) | View ranked applicant screening scores & evidence |

---

## 3. Core Contract Schemas & Payloads

### 3.1 Authentication & Context Switching

#### `POST /api/v1/auth/register`
- **Request**:
```json
{
  "email": "alex.candidate@gmail.com",
  "password": "Password123!",
  "full_name": "Alex Rivera"
}
```
- **Response**: `201 Created`
```json
{
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "email": "alex.candidate@gmail.com",
  "full_name": "Alex Rivera",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### `POST /api/v1/auth/switch-organization`
Allows a recruiter with multiple memberships to switch their active tenant context:
- **Request**:
```json
{
  "organization_id": "c1f3d3b7-7e62-4ef8-a401-44755e347aa9"
}
```
- **Response**: `200 OK`
```json
{
  "message": "Switched active organization context.",
  "active_org_id": "c1f3d3b7-7e62-4ef8-a401-44755e347aa9",
  "org_name": "Acme Cloud Corp",
  "org_role": "OWNER",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 3.2 Candidate Resume Upload & Parsing

#### `POST /api/v1/candidate/resumes/upload`
Uploads a PDF resume, saves it to `./data/resumes/`, extracts text using PyMuPDF, and parses structured data with local Ollama (`qwen3:4b`).

- **Request**: `multipart/form-data`
  - `file`: PDF file stream (Max 10MB)
  - `title`: Optional custom title (e.g. "FullStack-2026.pdf")
- **Response**: `201 Created`
```json
{
  "resume_id": "7a35cb99-df41-4560-9fbb-f24fa48db182",
  "version_number": 1,
  "file_name": "Alex_Rivera_Resume.pdf",
  "file_size_bytes": 2261,
  "parsed_data": {
    "candidate_name": "Alex Rivera",
    "headline": "Senior Full Stack Engineer",
    "years_of_experience": 6.5,
    "top_skills": ["React", "TypeScript", "Node.js", "PostgreSQL", "Docker", "AWS"],
    "summary": "Product-focused Full Stack Engineer with over six years of experience building scalable web applications."
  },
  "created_at": "2026-11-19T07:10:00Z"
}
```

---

### 3.3 Candidate Job Application

#### `POST /api/v1/candidate/jobs/{job_id}/apply`
Submits an application referencing an immutable resume version.
- **Request**:
```json
{
  "resume_id": "7a35cb99-df41-4560-9fbb-f24fa48db182"
}
```
- **Response**: `201 Created`
```json
{
  "application_id": "app_991823a-f110",
  "job_id": "job_1234_fullstack",
  "submitted_resume_id": "7a35cb99-df41-4560-9fbb-f24fa48db182",
  "status": "SUBMITTED",
  "applied_at": "2026-11-19T07:11:00Z"
}
```

---

### 3.4 Recruiter Job Requisition Management

#### `POST /api/v1/recruiter/jobs`
Creates a structured requisition scoped to `active_org_id`.
- **Request**:
```json
{
  "title": "Full Stack Developer",
  "department": "Engineering",
  "location": "Remote",
  "status": "PUBLISHED",
  "description": "We are seeking a high-performing Full Stack Software Engineer to build scalable web apps...",
  "required_skills": ["React", "TypeScript", "Node.js", "PostgreSQL"],
  "preferred_skills": ["Docker", "AWS"],
  "minimum_years_experience": 4.0
}
```
- **Response**: `201 Created` (returns created job with `organization_id` bound to active context).

---

### 3.5 AI Screening & Deterministic Scoring

#### `POST /api/v1/recruiter/jobs/{job_id}/screen`
Triggers immediate deterministic evaluation across all active applicants for the job:
1. Fetches all `job_applications` where `job_id = :job_id` and `organization_id = :active_org_id`.
2. Compares each candidate's parsed skills and experience against the job's requirements.
3. Computes transparent component scores:
   $$S_{fit} = 0.60 \cdot S_{req\_skills} + 0.15 \cdot S_{pref\_skills} + 0.25 \cdot S_{experience}$$
4. Calls Ollama (`qwen3:4b`) to generate a 1-sentence analytical synthesis for each candidate.
5. Saves results to `screening_results` and marks `screening_runs.status = 'COMPLETED'`.
- **Response**: `200 OK`
```json
{
  "screening_run_id": "run_c92d5be3-3b68",
  "job_id": "job_1234_fullstack",
  "total_screened": 4,
  "status": "COMPLETED",
  "completed_at": "2026-11-19T07:12:00Z"
}
```

#### `GET /api/v1/recruiter/jobs/{job_id}/screening-results`
- **Response**: `200 OK`
```json
{
  "screening_run_id": "run_c92d5be3-3b68",
  "job_id": "job_1234_fullstack",
  "total_screened": 4,
  "results": [
    {
      "result_id": "res_88192_uuid",
      "application_id": "app_991823a-f110",
      "candidate_id": "cand_001_uuid",
      "candidate_name": "Alex Rivera",
      "final_score": 93.8,
      "score_breakdown": {
        "required_skills_score": 100.0,
        "preferred_skills_score": 100.0,
        "experience_score": 100.0
      },
      "matched_skills": ["React", "TypeScript", "Node.js", "PostgreSQL", "Docker", "AWS"],
      "missing_skills": [],
      "experience_assessment": "MEETS_REQUIREMENT (6.5 / 4.0 Years)",
      "reasoning": "Candidate demonstrates all required core technologies with 6.5 years of verified engineering experience. Strong fit for the full stack engineering team."
    }
  ]
}
```

#### `PUT /api/v1/recruiter/applications/{id}/status`
Allows recruiters to advance candidate status in the hiring pipeline:
- **Request**:
```json
{
  "status": "SHORTLISTED"
}
```
- **Response**: `200 OK` (returns updated application).
