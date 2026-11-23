# TalentLens — Known Technical Limitations & Operational Boundary Notes

This document catalogues intentional architectural decisions, temporary operational constraints, and known system boundaries in the current release of TalentLens.

---

## 1. Local AI Inference & Concurrency Limits

- **Hardware Protection Semaphore:**
  - In local and low-memory staging environments (such as Apple Silicon M2 8GB), Ollama model inference is gated by a global async semaphore (`asyncio.Semaphore(1)`).
  - *Impact:* Simultaneous AI screening runs or assistant queries are executed sequentially. While this guarantees the host machine never crashes or runs out of RAM, queuing latency can increase under burst concurrent loads.
  - *Production Path:* Deploy Ollama or vLLM on a dedicated GPU cluster (e.g. NVIDIA A10G/T4 on AWS ECS/EKS) with horizontal auto-scaling and an asynchronous worker queue (e.g., Celery/ARQ with Redis).

- **Inference Latency:**
  - Local inference with 4B parameter models (`qwen3:4b`) typically takes 8–25 seconds depending on prompt size and token budget.
  - *Mitigation:* The system includes automatic 25-second timeouts and multi-tier fallbacks (Primary Model $\rightarrow$ Fallback Model $\rightarrow$ Deterministic Rule-Based Engine).

---

## 2. Rate Limiting Architecture

- **In-Memory Sliding Window Implementation:**
  - Rate limiting is currently implemented using an in-memory sliding-window counter in `backend/app/core/rate_limit.py`.
  - *Impact:* Rate limits are tracked per process. If backend services are horizontally scaled across multiple pods or container instances without sticky sessions, each pod maintains an independent counter.
  - *Production Path:* Replace in-memory dictionary storage with Redis sliding-window zset rate limiting (`redis-py`).

---

## 3. Resume PDF Parsing Capabilities

- **Digital vs. Scanned Documents:**
  - PyMuPDF (`fitz`) extracts digital text layers embedded within PDF documents.
  - *Behavior on Scanned / Flat Image PDFs:* Resumes that are image-only scans without optical character recognition (OCR) will fail the 15-word threshold and receive status `FAILED` with a user-friendly error instructing the candidate to upload a text-based PDF.
  - *Production Path:* Integrate an asynchronous OCR fallback pipeline (e.g. Tesseract or AWS Textract) triggered only when digital text extraction yields insufficient characters.

---

## 4. Multi-Tenant Organization Context

- **Session Context Binding via JWT:**
  - Organization context is selected via `/api/v1/auth/switch-organization` and bound directly into the JWT token payload (`active_org_id`, `org_role`).
  - *Impact:* If an organization owner revokes a recruiter's membership or downgrades their role, the recruiter's existing access token remains technically valid until its expiry (default 60 minutes) unless token revocation or database validation is enforced per request.
  - *Mitigation:* All sensitive recruiter endpoints query `get_active_recruiter_context` which cross-checks active membership status in PostgreSQL on every request.
