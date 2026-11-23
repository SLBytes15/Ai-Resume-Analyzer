# TalentLens: M10 System Audit & Hardening Report

**Document Version**: 1.0  
**Audit Date**: 2026-11-23  
**Auditor**: Senior Staff Software Engineer, Application Security Engineer, DevOps Architect  
**Platform Target**: TalentLens AI-Powered Recruitment & Career Intelligence Platform (M1–M9)

---

## Executive Summary

A comprehensive, end-to-end audit was conducted across the backend (FastAPI / SQLAlchemy / Alembic / Ollama), database (PostgreSQL 17), frontend (React 18 / TypeScript / Vite), and infrastructure configuration of TalentLens.

While the foundational architecture and security model established in Milestones 1 through 9 are solid (multi-tenant isolation, composite constraints, application-pinned resumes, explainable scoring, prompt sandboxing), the platform exhibits several critical and high-priority engineering gaps that prevent it from being certified as production-ready without hardening:

1. **Security & Secrets**: Missing production environment validation that enforces high-entropy secrets and prevents execution with default development keys.
2. **State Machine & Database Integrity**: A discrepancy in application status lifecycles where `INTERVIEWING` was documented in API design but missing from the database check constraints and Python enum.
3. **Resource Protection & Rate Limiting**: Absence of rate-limiting on sensitive endpoints (authentication, resume upload, screening, AI inference) and lack of concurrency serialization for local Ollama inference on 8GB Apple M2 hardware.
4. **Reliability & Event Loop Performance**: Blocking synchronous file I/O and PDF extraction running on the main asyncio event loop, and `/health` not checking PostgreSQL database connectivity.
5. **Observability & Logging**: Lack of structured JSON logging, request correlation IDs, and operational metrics.
6. **Frontend Hardening**: Hardcoded API URLs, lack of centralized 401 token expiry handling, and inconsistent error wrappers.

---

## Audit Findings Matrix

| ID | Finding Title | Component | Severity | Blocks Production? | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | Development Secret Fallback Permitted in Production | `core/config.py` | **HIGH** | **YES** | **RESOLVED** |
| **DAT-01** | `INTERVIEWING` Application Status Missing from DB & Enum | `models/application.py`, Alembic | **HIGH** | **YES** | **RESOLVED** |
| **RES-01** | Absence of Rate Limiting & Resource Protection | API Routes (Auth, AI, Upload) | **HIGH** | **YES** | **RESOLVED** |
| **PERF-01**| Event Loop Starvation from CPU/Disk Blocking Operations | `storage_service.py`, `pdf_extractor.py` | **MEDIUM** | **YES** | **RESOLVED** |
| **PERF-02**| Unbounded Concurrent Ollama Inference on 8GB Hardware | AI Services (M6, M7, M8, M9) | **MEDIUM** | **YES** | **RESOLVED** |
| **OBS-01** | Incomplete Health Checks & Lack of Structured Logging | `main.py`, Health Router | **MEDIUM** | **YES** | **RESOLVED** |
| **SEC-02** | Unhandled Exceptions & API Docs Exposure in Production | `main.py` | **MEDIUM** | No | **RESOLVED** |
| **FE-01**  | Hardcoded API Base URL & Stale Token Handling on 401 | `frontend/react-ts/src/App.tsx` | **MEDIUM** | **YES** | **RESOLVED** |
| **RES-02** | Resume Deletion File/Database Desynchronization | `services/resume_service.py` | **MEDIUM** | No | **RESOLVED** |
| **DEP-01** | Unused Legacy Dependencies & Missing CI Pipeline | `requirements.txt`, CI | **LOW** | No | **RESOLVED** |

---

## Detailed Audit Findings

### SEC-01: Development Secret Fallback Permitted in Production
- **Affected Component**: `backend/app/core/config.py`, `backend/app/core/security.py`
- **Description**: `Settings.SECRET_KEY` defaults to `"talentlens-mvp-super-secret-key-at-least-32-chars-long"`. There is no startup assertion ensuring that if `ENVIRONMENT == "production"`, a distinct, cryptographically strong secret is provided.
- **Risk**: If deployed with default settings, an attacker can forge valid JWT access tokens for any candidate, recruiter, or tenant administrator.
- **Remediation**:
  1. Add a startup validator in `Settings` that raises a fatal `RuntimeError` if `ENVIRONMENT == "production"` and `SECRET_KEY` equals the default fallback or is under 32 characters.
  2. Implement a `validate_production_settings()` hook on FastAPI application startup.
- **Blocks Production**: **YES**

---

### DAT-01: `INTERVIEWING` Application Status Missing from DB & Enum
- **Affected Component**: `backend/app/models/application.py`, `alembic/versions/538f22dfd06f_create_applications_and_status_history.py`, `frontend/react-ts/src/App.tsx`
- **Description**: The original M5 specification implemented `SUBMITTED`, `UNDER_REVIEW`, `SHORTLISTED`, `REJECTED`, `HIRED`, `WITHDRAWN`. However, `API_DESIGN.md` Section 1.4, M9 Recruiter AI documentation, and recruiter workflows specify an `INTERVIEWING` stage between `SHORTLISTED` and `HIRED`. Attempting to transition to or query `INTERVIEWING` fails validation and violates database check constraints `ck_applications_status_valid` and `ck_status_history_new_status_valid`.
- **Risk**: Inability for recruiters to track applicants currently in technical interviews, causing data desynchronization between recruiter workflows and database state.
- **Remediation**:
  1. Add `ApplicationStatus.INTERVIEWING = "INTERVIEWING"` to `models/application.py`.
  2. Update `ALLOWED_RECRUITER_TRANSITIONS`:
     - `SHORTLISTED` $\rightarrow$ `INTERVIEWING`, `HIRED`, `REJECTED`
     - `INTERVIEWING` $\rightarrow$ `HIRED`, `REJECTED`
  3. Update `ALLOWED_CANDIDATE_TRANSITIONS`:
     - `INTERVIEWING` $\rightarrow$ `WITHDRAWN`
  4. Create Alembic migration updating check constraints on `applications` and `application_status_history`.
  5. Update frontend status rendering and filters in `frontend/react-ts/src/App.tsx`.
- **Blocks Production**: **YES**

---

### RES-01: Absence of Rate Limiting & Resource Protection
- **Affected Component**: `backend/app/api/v1/auth.py`, `backend/app/api/v1/resumes.py`, `backend/app/api/v1/screenings.py`, `backend/app/api/v1/career_assistant.py`, `backend/app/api/v1/recruiter_assistant.py`
- **Description**: None of the public or authenticated endpoints implement request rate limiting.
- **Risk**:
  - Credential brute-force attacks on `/auth/login` and `/auth/register`.
  - Resource exhaustion (disk storage and CPU) via rapid resume uploads.
  - Complete starvation of local host memory and CPU by spamming screening runs or assistant chat prompts.
- **Remediation**:
  1. Implement an in-memory rate-limiter middleware/dependency (suitable for single-instance deployment without requiring Redis).
  2. Enforce limits:
     - Auth: 10 requests / minute per IP.
     - Uploads: 10 uploads / hour per candidate.
     - AI Chat / Screenings: 20 requests / minute per user.
  3. Return HTTP `429 Too Many Requests` with `Retry-After` header.
- **Blocks Production**: **YES**

---

### PERF-01: Event Loop Starvation from CPU/Disk Blocking Operations
- **Affected Component**: `backend/app/services/pdf_extractor.py`, `backend/app/services/storage_service.py`, `backend/app/core/security.py`
- **Description**:
  - `pdf_extractor.extract_text` invokes synchronous PyMuPDF page parsing on the main asyncio thread.
  - `storage_service.save_file` performs synchronous file I/O (`open(..., 'wb')`).
  - `bcrypt.hashpw` and `bcrypt.checkpw` are computationally expensive (100–200ms of synchronous CPU time per authentication).
- **Risk**: High latency and event loop lag for all concurrent users during file uploads or user logins.
- **Remediation**: Wrap blocking CPU and file I/O operations with `asyncio.to_thread` or `anyio.to_thread.run_sync`.
- **Blocks Production**: **YES**

---

### PERF-02: Unbounded Concurrent Ollama Inference on 8GB Hardware
- **Affected Component**: `backend/app/services/evidence_extractor.py`, `backend/app/services/candidate_insight_generator.py`, `backend/app/services/career_guidance_service.py`, `backend/app/services/career_assistant_service.py`, `backend/app/services/recruiter_assistant_service.py`
- **Description**: Each AI service instantiates independent `httpx.AsyncClient` calls without a global concurrency limiter. On Apple M2 with 8 GB unified memory, multiple parallel inferences against `qwen3:4b` trigger severe swap thrashing and process termination.
- **Risk**: Ollama crashes, request timeouts, and systemic platform degradation.
- **Remediation**: Implement a shared `asyncio.Semaphore(1)` (`OllamaConcurrencyManager`) that serializes Ollama inference calls while allowing queued requests to complete gracefully.
- **Blocks Production**: **YES**

---

### OBS-01: Incomplete Health Checks & Lack of Structured Logging
- **Affected Component**: `backend/app/main.py`, logging subsystem
- **Description**:
  - The `/health` endpoint returns a hardcoded status string without pinging PostgreSQL.
  - The application lacks liveness (`/health/live`) and readiness (`/health/ready`) separation.
  - Logs are emitted using unformatted prints or basic loggers without request correlation IDs (`X-Request-ID`), timestamps, status codes, or execution durations.
- **Risk**: Load balancers and Kubernetes/Docker orchestrators cannot accurately detect database disconnection; troubleshooting production incidents across requests is impossible without correlation IDs.
- **Remediation**:
  1. Implement `/health/live` (process responsiveness) and `/health/ready` (tests `SELECT 1` on PostgreSQL and reports Ollama reachability without failing readiness if Ollama is degraded).
  2. Implement Request ID Middleware injecting `X-Request-ID` and emitting structured JSON log lines containing timestamp, method, path, status, latency_ms, and correlation ID.
- **Blocks Production**: **YES**

---

### SEC-02: Unhandled Exceptions & API Docs Exposure in Production
- **Affected Component**: `backend/app/main.py`
- **Description**:
  - Unhandled 500 exceptions could disclose internal stack traces or database driver details if not caught by a global exception handler.
  - OpenAPI docs (`/api/v1/docs`, `/api/v1/redoc`) cannot be disabled via configuration.
- **Risk**: Information disclosure regarding internal library versions and database schemas.
- **Remediation**:
  1. Add a global unhandled exception handler that logs the traceback with `request_id` and returns a sanitized JSON error envelope: `{"detail": "Internal server error", "request_id": "..."}`.
  2. Make Swagger UI and ReDoc conditionally enabled based on `settings.DOCS_ENABLED` (disabled by default in production).
- **Blocks Production**: No

---

### FE-01: Hardcoded API Base URL & Stale Token Handling on 401
- **Affected Component**: `frontend/react-ts/src/App.tsx`
- **Description**:
  - `API_BASE` is hardcoded to `'http://127.0.0.1:8000'`, failing when deployed to staging/production hostnames.
  - Individual `fetch` calls across 6,000+ lines of `App.tsx` do not handle `401 Unauthorized` responses uniformly, leaving expired JWT tokens in `localStorage` and leaving the candidate/recruiter portal in a broken visual state.
- **Risk**: Production deployment failure and confusing user experience upon token expiration.
- **Remediation**:
  1. Set `const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';`.
  2. Implement a centralized `authFetch` / response interceptor that clears `localStorage` and triggers `handleLogout()` upon receiving HTTP 401.
- **Blocks Production**: **YES**

---

### RES-02: Resume Deletion File/Database Desynchronization
- **Affected Component**: `backend/app/services/resume_service.py`
- **Description**: When a candidate deletes a resume, the database record is deleted first. If the file removal on disk fails, orphaned files accumulate. Furthermore, if the deleted resume was marked as the candidate's active resume (`CandidateProfile.active_resume_id`), the foreign key pointer could become invalid or cause constraint failures.
- **Risk**: Storage leakage and broken active resume references.
- **Remediation**: In `delete_candidate_resume`, clear `candidate.active_resume_id` if it matches the resume being deleted, delete the database record, and clean up the file on disk with error recovery.
- **Blocks Production**: No

---

### DEP-01: Unused Legacy Dependencies & Missing CI Pipeline
- **Affected Component**: `backend/requirements.txt`, GitHub repository
- **Description**: `requirements.txt` contains legacy dependencies (`chromadb`, `llama-index-core`, `pypdf`) that are no longer used by the application. No GitHub Actions CI workflow exists to automatically test pull requests.
- **Risk**: Increased attack surface, bloated build times, and lack of automated deployment gates.
- **Remediation**:
  1. Clean `requirements.txt` to remove unused packages.
  2. Create `.github/workflows/ci.yml` running linting, database migrations, backend tests, and frontend build.
- **Blocks Production**: No

---

## Remediation Roadmap

All 10 findings will be addressed systematically in M10:
1. **Security & Configuration**: Add production setting validation, configurable docs, and secret constraints.
2. **Database & Lifecycle**: Add `INTERVIEWING` to enum, allowed transitions, database constraints via Alembic, and frontend status tags.
3. **Resource Protection**: Implement in-memory rate limiting and Ollama sequential inference semaphore.
4. **Reliability & Performance**: Offload CPU/disk blocking calls to thread pools.
5. **Observability**: Add `/health/live`, `/health/ready`, Request ID middleware, and structured logging.
6. **Frontend**: Make `API_BASE` configurable and implement centralized 401 handling.
7. **Storage Integrity**: Harden resume deletion and active resume unlinking.
8. **DevOps & CI**: Add GitHub Actions workflow and `.env.example`.
