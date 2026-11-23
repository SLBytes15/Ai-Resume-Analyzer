# TalentLens: RESTful API Design Specification

**Document Version**: 4.0  
**API Standard**: OpenAPI 3.1 / FastAPI  
**Base URL**: `/api/v1`  
**Authentication**: Bearer JWT (`Authorization: Bearer <token>`)  

---

## Version 4 Corrections

The following authoritative API corrections have been implemented in Version 4:
1. **Idempotency Architecture**: Implemented database-backed idempotency using the `idempotency_keys` table for `POST /candidate/jobs/{id}/apply` and `POST /recruiter/jobs/{id}/screenings`, with request body hashing, concurrent lock handling, and 24-hour response caching.
2. **Hardened Token Lifecycles & Refresh Rotation**: Documented 15-minute access token lifespan, single-use refresh token rotation with token family breach invalidation, and immediate membership revocation enforcement.
3. **Upload Security & Magic-Byte Inspection**: Added binary signature inspection (`%PDF-` for PDF, `PK\x03\x04` for DOCX), strict 10MB size limits, sanitized UUID storage keys, and 15-minute expiring download URLs.
4. **Information Leakage Prevention**: Standardized on returning `404 Not Found` rather than `403 Forbidden` for cross-tenant resource lookups to prevent tenant enumeration attacks.
5. **Rejection Reason Confidentiality**: Explicitly excluded `rejection_reason` and internal recruiter notes from all candidate-facing application endpoints.
6. **Application Status State Machine**: Enforced valid state transitions (`SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `SHORTLISTED` / `REJECTED` $\rightarrow$ `INTERVIEWING` $\rightarrow$ `HIRED`) with API validation.
7. **Screening Snapshot Reproducibility Meta**: Extended screening run responses with `resume_content_hash`, `job_version`, `model_version`, `prompt_version`, `taxonomy_version`, and `pipeline_version`.

---

## 1. Authentication, Token Lifecycles & Security

### 1.1 Token Lifetime & Rotation
- **Access Token**: Short-lived (15 minutes). Contains `sub` (user_id), `email`, `system_role`, and active `org_id` / `org_role`.
- **Refresh Token**: Long-lived (7 days). Single-use only.
- **Token Family Rotation**: Stored in PostgreSQL. When a refresh token is used, a new access/refresh pair is issued and the old refresh token is marked used. If a previously used refresh token is submitted (indicating token theft), the entire token family is immediately revoked.
- **Revocation Check**: Every request validates that `organization_memberships.is_active = TRUE` and `status = 'ACTIVE'` for the active organization.

### 1.2 Context-Aware JWT Structure
```json
{
  "sub": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "email": "sarah.recruiter@talentcorp.com",
  "system_role": "PLATFORM_USER",
  "active_org_id": "c1f3d3b7-7e62-4ef8-a401-44755e347aa9",
  "org_role": "RECRUITER",
  "token_family": "fam_a8f3b92",
  "exp": 1720000900
}
```

---

## 2. Global Standards & Error Envelopes

### 2.1 Standard Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested requisition does not exist.",
    "details": []
  },
  "meta": {
    "timestamp": "2026-11-19T00:45:00Z",
    "request_id": "req_88f91040-5cf0"
  }
}
```
*(Cross-tenant attempts return `RESOURCE_NOT_FOUND` rather than `PERMISSION_DENIED` to prevent resource enumeration).*

### 2.2 Standard Paginated Envelope
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "total_count": 42,
    "limit": 20,
    "offset": 0,
    "has_next": true
  },
  "meta": {
    "timestamp": "2026-11-19T00:45:00Z",
    "request_id": "req_88f91040-5cf0"
  }
}
```

---

## 3. API Endpoint Matrix

| Domain | Method | Path | Role / Context | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/auth/register` | Public | Register new candidate or recruiter |
| **Auth** | `POST` | `/auth/login` | Public | Authenticate user, return access + refresh tokens |
| **Auth** | `POST` | `/auth/refresh` | Public | Rotate refresh token, return new access token |
| **Auth** | `POST` | `/auth/logout` | Authenticated | Revoke refresh token and invalidate session |
| **Auth** | `POST` | `/auth/switch-context` | Authenticated | Switch active recruiter organization context |
| **Auth** | `GET` | `/auth/me` | Authenticated | Get current authenticated user profile & memberships |
| **Organizations** | `POST` | `/organizations` | Authenticated | Create a new organization (User becomes `OWNER`) |
| **Organizations** | `GET` | `/organizations/my-memberships` | Authenticated | List all organizations the user belongs to |
| **Organizations** | `POST` | `/organizations/{id}/invites` | `ADMIN`+ | Invite member with specified role |
| **Organizations** | `PUT` | `/organizations/{id}/members/{user_id}/role` | `ADMIN`+ | Update member role (`OWNER` required to transfer) |
| **Candidate Profile**| `GET` | `/candidate/profile` | Candidate | Retrieve personal candidate profile |
| **Candidate Profile**| `PUT` | `/candidate/profile` | Candidate | Update personal candidate profile |
| **Candidate Resumes**| `POST` | `/candidate/resumes/upload` | Candidate | Upload resume PDF/DOCX (Max 10MB, magic-byte checked) |
| **Candidate Resumes**| `GET` | `/candidate/resumes` | Candidate | List all uploaded resume versions |
| **Candidate Resumes**| `GET` | `/candidate/resumes/{id}/status`| Candidate | Poll resume ingestion & quality analysis status |
| **Candidate Resumes**| `GET` | `/candidate/resumes/{id}` | Candidate | Get parsed profile & objective quality breakdown |
| **Candidate Resumes**| `GET` | `/candidate/resumes/{id}/download`| Candidate | Get 15-minute download URL for candidate's own resume |
| **Candidate Jobs** | `GET` | `/jobs` | Public / Candidate | Search & list published job openings |
| **Candidate Apps** | `POST` | `/candidate/jobs/{id}/apply` | Candidate | Submit application with specific `resume_id` (Idempotent) |
| **Candidate Apps** | `GET` | `/candidate/applications` | Candidate | List submitted applications with tracking statuses |
| **Candidate Coach** | `POST` | `/candidate/assistant/chat` | Candidate | Career coach RAG (Scoped strictly to candidate's resumes) |
| **Recruiter Jobs** | `POST` | `/recruiter/jobs` | Recruiter (`org_id`)| Create job requisition with structured requirements |
| **Recruiter Jobs** | `GET` | `/recruiter/jobs` | Recruiter (`org_id`)| List organization's jobs with applicant counts |
| **Recruiter Jobs** | `GET` | `/recruiter/jobs/{id}` | Recruiter (`org_id`)| Get detailed job requisition and requirements |
| **Recruiter Jobs** | `PUT` | `/recruiter/jobs/{id}` | Recruiter (`org_id`)| Update job requirements (increments `version_number`) |
| **Recruiter Apps** | `GET` | `/recruiter/jobs/{id}/applications` | Recruiter (`org_id`)| List applications submitted to specific job |
| **Recruiter Apps** | `PUT` | `/recruiter/applications/{id}/status`| Recruiter (`org_id`)| Advance application status in state machine |
| **Recruiter Apps** | `GET` | `/recruiter/applications/{id}/resume/download`| Recruiter (`org_id`)| Download the immutable resume version submitted to this job |
| **Screening** | `POST` | `/recruiter/jobs/{id}/screenings` | Recruiter (`org_id`)| Trigger bulk screening run (Idempotent via config hash) |
| **Screening** | `GET` | `/recruiter/screenings/{id}/status` | Recruiter (`org_id`)| Poll screening run progress |
| **Screening** | `GET` | `/recruiter/screenings/{id}/results`| Recruiter (`org_id`)| Get ranked candidate matches with explainable breakdown |
| **Recruiter Copilot**| `POST` | `/recruiter/jobs/{id}/assistant/chat` | Recruiter (`org_id`)| Requisition copilot RAG (Scoped strictly to job applicants) |

---

## 4. Idempotency Specification

### 4.1 Client Request Header
For state-modifying requests (`/apply` and `/screenings`), clients provide an optional header:
`Idempotency-Key: <unique-uuid-or-string>`

### 4.2 Database Idempotency Mechanics
1. When a request arrives, the server computes a SHA-256 fingerprint of the request payload + user ID + endpoint path.
2. The server queries `public.idempotency_keys` where `key = :key AND user_id = :user_id`.
3. If an entry exists and `request_hash` matches:
   - Return cached HTTP status and response body immediately (`200 OK`).
4. If an entry exists but `request_hash` differs:
   - Return `409 Conflict` (key reused with different payload).
5. If no entry exists:
   - Acquire a distributed lock / row-level insert, execute the transaction, record the response in `idempotency_keys` with an expiration timestamp (`created_at + 24 hours`), and commit.

---

## 5. Upload Validation & Security

### 5.1 Binary Signature Inspection
The backend inspects the initial 512 bytes of uploaded files:
- **PDF**: Must begin with bytes `%PDF-` (`0x25 0x50 0x44 0x46 0x2D`).
- **DOCX**: Must begin with ZIP archive signature `PK\x03\x04` (`0x50 0x4B 0x03 0x04`).
- Any file with an invalid signature is rejected immediately with `415 Unsupported Media Type` before writing to disk.

### 5.2 Storage Key Sanitization
All files are saved under non-guessable, deterministic keys:
`candidates/{candidate_user_id}/resumes/{resume_uuid}/original_{sanitized_basename}.pdf`
Filenames are stripped of path traversals (`../`), control characters, and non-ASCII glyphs.

---

## 6. Sample API Contracts

### 6.1 Candidate Job Application Submission
- **Request**: `POST /api/v1/candidate/jobs/{job_id}/apply`
- **Headers**: `Idempotency-Key: 7c9e6679-7425-40de-944b-e07fc1f90ae7`
- **Body**: `{"resume_id": "7a35cb99-df41-4560-9fbb-f24fa48db182"}`
- **Response**: `201 Created`
```json
{
  "success": true,
  "data": {
    "application_id": "app_991823a-f110",
    "job_id": "job_1234_fullstack",
    "submitted_resume_id": "7a35cb99-df41-4560-9fbb-f24fa48db182",
    "status": "SUBMITTED",
    "applied_at": "2026-11-19T00:46:00Z"
  }
}
```

### 6.2 Candidate Viewing Application (No Recruiter Rejection Notes)
- **Request**: `GET /api/v1/candidate/applications`
- **Response**: `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "application_id": "app_991823a-f110",
      "job_id": "job_1234_fullstack",
      "job_title": "Senior Full Stack Engineer",
      "organization_name": "TalentCorp",
      "status": "UNDER_REVIEW",
      "applied_at": "2026-11-19T00:46:00Z",
      "updated_at": "2026-11-19T00:48:00Z"
    }
  ]
}
```
*(Notice: `rejection_reason` is strictly omitted from the candidate response contract).*

### 6.3 Recruiter Bulk Screening Results with Reproducibility Metadata
- **Request**: `GET /api/v1/recruiter/screenings/{screening_run_id}/results`
- **Response**: `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "result_id": "res_88192_uuid",
      "application_id": "app_991823a-f110",
      "candidate_id": "1141bc22-386d-472d-8e6d-6218d89e5a1b",
      "candidate_name": "Alex Rivera",
      "resume_content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "final_score": 93.0,
      "scoring_status": "SCORED",
      "score_breakdown": {
        "required_skills_score": 100.0,
        "preferred_skills_score": 80.0,
        "experience_score": 100.0,
        "semantic_similarity_score": 85.0,
        "evidence_coverage": 1.0,
        "uncertainty_score": 0.0
      },
      "experience_summary": {
        "candidate_years": 6.5,
        "required_years": 4.0,
        "status": "MEETS_REQUIREMENT"
      },
      "demonstrated_skills": ["React", "TypeScript", "Node.js", "PostgreSQL"],
      "unestablished_skills": [],
      "explicitly_absent_skills": [],
      "evidence_snippets": [
        {
          "skill": "PostgreSQL",
          "quote": "Core relational database data persistence layers structured around PostgreSQL.",
          "section": "Professional Work History"
        }
      ],
      "ai_reasoning_summary": "Candidate demonstrates all required core technologies with 6.5 years of verified engineering experience. Production Node.js and PostgreSQL evidence verified."
    }
  ],
  "reproducibility_meta": {
    "screening_run_id": "c92d5be3-3b68-45e0-94cb-0bfdb9486c47",
    "job_id": "job_1234_fullstack",
    "job_version": 1,
    "model_version": "qwen3:4b",
    "fallback_model_version": "llama3.2:1b",
    "embedding_version": "nomic-embed-text",
    "prompt_version": "v1.0.0",
    "taxonomy_version": "v1.0.0",
    "pipeline_version": "v1.0.0",
    "completed_at": "2026-11-19T00:46:30Z"
  },
  "pagination": {
    "total_count": 18,
    "limit": 20,
    "offset": 0,
    "has_next": false
  }
}
```

---

## 7. Milestone 7: Candidate Resume Intelligence & Career Guidance API

### 7.1 Request Resume Analysis
- **Route**: `POST /api/v1/resumes/{resume_id}/analyze`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Request Body**:
  ```json
  {
    "target_role": "Backend Developer"
  }
  ```
- **Responses**:
  - `201 Created`: Complete analysis report.
  - `404 Not Found`: Resume does not exist or belongs to another candidate.
  - `409 Conflict`: Duplicate analysis for this resume and target role already in progress.
  - `422 Unprocessable Content`: Resume has insufficient extracted text.

### 7.2 List Historical Analyses for Resume
- **Route**: `GET /api/v1/resumes/{resume_id}/analyses`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "f512db34-9ead-4780-a2c3-799ac17ca15b",
      "resume_id": "893c5be3-3b68-45e0-94cb-0bfdb9486c47",
      "target_role": "Backend Developer",
      "status": "COMPLETED",
      "overall_summary": "Strong backend candidate with practical API engineering experience...",
      "created_at": "2026-11-23T10:00:00Z"
    }
  ]
  ```

### 7.3 Get Analysis Detail
- **Route**: `GET /api/v1/analyses/{analysis_id}`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Response `200 OK`**: Complete `ResumeAnalysisResponse` including `deterministic_checks` and `analysis_data`.

### 7.4 Retry Failed Analysis
- **Route**: `POST /api/v1/analyses/{analysis_id}/retry`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Responses**:
  - `200 OK`: Re-executed analysis.
  - `400 Bad Request`: If analysis status is not `FAILED`.

---

## 8. Milestone 8: Candidate AI Career Assistant Endpoints

### 8.1 Create Career Conversation
- **Route**: `POST /api/v1/career/conversations`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Payload**:
  ```json
  {
    "resume_id": "893c5be3-3b68-45e0-94cb-0bfdb9486c47",
    "target_role": "Senior Backend Engineer",
    "conversation_purpose": "ROLE_TRANSITION",
    "title": "Backend Transition Strategy",
    "initial_message": "What skills do I need to demonstrate for Senior Backend roles?"
  }
  ```
- **Responses**:
  - `201 Created`: `CareerConversationResponse` (if initial message provided, assistant reply is pre-generated).
  - `404 Not Found`: If specified resume does not exist or belong to candidate.

### 8.2 List Candidate Career Conversations
- **Route**: `GET /api/v1/career/conversations`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Query Params**: `is_archived` (optional bool), `limit` (int, 1-100), `offset` (int)
- **Response `200 OK`**: List of `CareerConversationResponse` with message counts and last message previews.

### 8.3 Get Full Conversation Thread
- **Route**: `GET /api/v1/career/conversations/{conversation_id}`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Response `200 OK`**: Complete `CareerConversationDetailResponse` including chronological `messages` list with context metadata.
- **Response `404 Not Found`**: Conversation does not exist or belongs to another user.

### 8.4 Post Message in Conversation
- **Route**: `POST /api/v1/career/conversations/{conversation_id}/messages`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Payload**:
  ```json
  {
    "content": "Generate 3 technical interview questions based on my projects.",
    "include_m7_analysis": true
  }
  ```
- **Responses**:
  - `201 Created`:
    ```json
    {
      "user_message": { "id": "...", "role": "USER", "content": "..." },
      "assistant_message": {
        "id": "...",
        "role": "ASSISTANT",
        "content": "...",
        "context_metadata": {
          "resume_id": "...",
          "retrieved_sections": ["projects", "skills"],
          "evidence_snippets": ["..."],
          "is_fallback": false
        }
      }
    }
    ```
  - `404 Not Found`: If conversation does not exist or candidate is unauthorized.

### 8.5 Update Conversation
- **Route**: `PATCH /api/v1/career/conversations/{conversation_id}`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Payload**: `{ "conversation_title": "New Title", "is_archived": true }`
- **Response `200 OK`**: Updated `CareerConversationResponse`.

### 8.6 Delete Conversation
- **Route**: `DELETE /api/v1/career/conversations/{conversation_id}`
- **Auth**: Candidate JWT (`Bearer <token>`)
- **Response `204 No Content`**: Cascades and deletes conversation and all message records.
