# TalentLens: Production Security Checklist & Verification

**Document Version**: 1.0  
**Scope**: Production Pre-Flight Security Audit for TalentLens Platform (M1–M10)

---

## 1. Authentication & Secrets

- [x] **No Default Secrets in Production**: Startup check fails fatally if default `SECRET_KEY` is detected in `production`.
- [x] **Secret Key Entropy**: Minimum 32 characters enforced at startup for production mode.
- [x] **Secure Password Hashing**: Passwords hashed with bcrypt and random salt; offloaded to async thread pool to prevent event loop blocking.
- [x] **Token Lifetimes**: Access tokens configured with sensible expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- [x] **Token Revocation / Inactive User Blocking**: User `is_active` checked on every authenticated request; inactive accounts rejected immediately with HTTP 401.

---

## 2. Multi-Tenant Authorization & IDOR Defense

- [x] **Database-Resolved Active Context**: Recruiter context resolved from verified database membership (`organization_memberships.is_active = TRUE`), never from client-supplied request bodies alone.
- [x] **Tenant Scoping on Queries**: All job, application, screening, and assistant queries explicitly filtered by `organization_id`.
- [x] **Cross-Tenant IDOR Prevention**: Attempting to query another organization's job, application, or screening returns `404 Not Found` (preventing tenant resource enumeration).
- [x] **Role Hierarchy Enforcement**: Read-only `VIEWER` role forbidden from mutating jobs, status, or screening runs.
- [x] **Candidate Privacy Boundaries**:
  - Candidate career conversations (M8) completely hidden from recruiters (`404 Not Found`).
  - Candidate resume intelligence (M7) completely hidden from recruiters.
  - Recruiters can only access resume files explicitly submitted to a job owned by their active organization.

---

## 3. Resume Upload & Storage Security

- [x] **File Extension Validation**: Strict `.pdf` check.
- [x] **Magic-Byte Signature Verification**: Binary check for `%PDF-` header magic bytes.
- [x] **File Size Enforcement**: Strict maximum size (`5 MB`, configurable via `MAX_UPLOAD_SIZE_BYTES`).
- [x] **Directory Traversal Defense**: Storage paths generated as UUIDs (`{candidate_id}/{resume_id}.pdf`); safe resolution verifies paths remain strictly within `UPLOAD_DIR`.
- [x] **Submitted Resume Immutability**: Resumes pinned to submitted job applications cannot be modified or deleted (`HTTP 409 Conflict`).

---

## 4. Prompt Injection & AI Security

- [x] **Untrusted Input Fencing**: All candidate resume texts and job descriptions fenced within `<untrusted_candidate_resume>` and `<verified_organization_data>` tags.
- [x] **System Instruction Preservation**: Anti-injection instructions instruct LLM to ignore embedded commands.
- [x] **Non-Autonomous Decision Support**: LLMs cannot mutate application statuses, change screening scores, or make hiring decisions.
- [x] **Fairness & Anti-Bias Directives**: Explicit system prompts ban evaluation on age, gender, race, religion, disability, or pedigree indicators.
- [x] **Deterministic Fallback**: If Ollama is offline or times out, rule-based fallback generates safe, structured data without crashing.

---

## 5. Network, API & Infrastructure Security

- [x] **Rate Limiting**: In-memory rate limiting applied to auth, resume upload, screening, and AI chat endpoints.
- [x] **Ollama Concurrency Limiter**: Sequential inference semaphore prevents host memory exhaustion on 8GB Apple M2 hardware.
- [x] **Health Probes**: Liveness (`/health/live`) and Readiness (`/health/ready`) probe endpoints implemented.
- [x] **Exception Masking**: Global exception handler masks unhandled 500 exceptions, returning correlation IDs without leaking internal stack traces.
- [x] **Configurable API Documentation**: `docs_url` and `redoc_url` toggleable via `DOCS_ENABLED` (disabled in production).
- [x] **CORS Configuration**: Restrictive `CORS_ORIGINS` configurable via environment variables.
