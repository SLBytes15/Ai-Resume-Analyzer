# TalentLens — Release Deployment Checklist

This operational checklist must be executed before, during, and after deploying TalentLens to staging or production environments.

---

## 1. Pre-Deployment Checklist

- [ ] **Infrastructure & Environment Verification:**
  - [ ] Target PostgreSQL server is running version 16+ with SSL enabled.
  - [ ] Target Ollama service is reachable with required local models pulled (`qwen3:4b`, `llama3.2:1b`, `nomic-embed-text:latest`).
  - [ ] File storage directory (`UPLOAD_DIR`) exists, has adequate disk space, and is writable by the application service user.
- [ ] **Configuration & Secrets Sanitization:**
  - [ ] Ensure `ENVIRONMENT` is set to `staging` or `production` (never `development`).
  - [ ] Ensure `SECRET_KEY` is set to a secure, cryptographically random string ($\ge 32$ characters) generated via `openssl rand -hex 32`.
  - [ ] Verify `CORS_ORIGINS` contains only verified HTTPS client domains (no wildcard `*` allowed).
  - [ ] Verify `DOCS_ENABLED=false` in production to prevent exposing Swagger OpenAPI endpoints publicly.
- [ ] **Database Pre-flight & Backup:**
  - [ ] Run pre-deployment snapshot backup:
    ```bash
    pg_dump -h <DB_HOST> -U <DB_USER> -d <DB_NAME> -F c -b -f /backup/pre_deploy_$(date +%Y%m%d_%H%M%S).dump
    ```
  - [ ] Verify pre-deployment backup file size and integrity.

---

## 2. Deployment Execution Checklist

- [ ] **Database Migrations:**
  - [ ] Run Alembic migration to head:
    ```bash
    cd backend && alembic upgrade head
    ```
  - [ ] Confirm migration revision matches repository head:
    ```bash
    alembic current
    # Expected head: 27af204e3f76
    ```
- [ ] **Application Service Startup:**
  - [ ] Start backend FastAPI service (e.g. via Uvicorn/Gunicorn worker process manager):
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    ```
  - [ ] Deploy compiled frontend static build from `frontend/react-ts/dist` to web server (Nginx / Cloudflare Pages / Caddy).
- [ ] **Probes & Readiness Verification:**
  - [ ] Check liveness probe:
    ```bash
    curl -f http://localhost:8000/health/live
    # Expected: {"status":"live"} (HTTP 200)
    ```
  - [ ] Check readiness probe:
    ```bash
    curl -f http://localhost:8000/health/ready
    # Expected: {"status":"ready","database":"healthy"} (HTTP 200)
    ```

---

## 3. Post-Deployment Verification & Smoke Testing

- [ ] **Auth & Session Smoke Test:**
  - [ ] Register a new test candidate and verify JWT receipt.
  - [ ] Test login and verify `/api/v1/auth/me`.
- [ ] **Candidate Journey Smoke Test:**
  - [ ] Upload a test PDF resume and confirm status transitions to `COMPLETED`.
  - [ ] View publicly listed published jobs.
  - [ ] Submit job application with pinned resume version.
- [ ] **Recruiter Journey Smoke Test:**
  - [ ] Log in as recruiter, select active organization context.
  - [ ] Review applicants for published job requisition.
  - [ ] Trigger an AI candidate screening run and verify explainable scores and recruiter insights.
  - [ ] Transition applicant status: `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `SHORTLISTED` $\rightarrow$ `INTERVIEWING`.
- [ ] **Security Smoke Test:**
  - [ ] Verify cross-tenant access to another organization's jobs or applications returns HTTP 404.
  - [ ] Verify `VIEWER` role cannot mutate job or applicant statuses (HTTP 403).
  - [ ] Verify `X-Request-ID` is present on all response headers.
- [ ] **Logging & Monitoring:**
  - [ ] Confirm JSON structured logs are emitting with request IDs and appropriate log levels.
  - [ ] Confirm no 5xx unhandled exceptions in APM/monitoring dashboard.
