# TalentLens: Architectural Decision Records (ADRs)

**Document Version**: 4.0  
**Status**: Authoritative Architectural Decisions  
**Author**: Principal Software Architect, PostgreSQL Security Specialist, AI Systems Engineer  

---

## Version 4 Corrections

The following authoritative decisions have been updated in Version 4:
1. **Active Context Derivation & Anti-Spoofing (ADR-001)**: The active organization context must be derived exclusively from verified JWT authentication claims, never from client-supplied request bodies. Helper `fn_has_active_org_membership` verifies both user and organization contexts.
2. **Complete RLS & Security-Definer Hardening (ADR-002)**: Added `ENABLE/FORCE RLS` to `organizations`. Specified safe `search_path = pg_catalog, public` and dedicated schema owner `talentlens_admin` for security-definer functions.
3. **Composite Foreign Key Anti-IDOR & Trigger Immutability (ADR-003)**: Relational schema enforces candidate resume ownership at the foreign key level and database triggers lock submitted resumes and completed screening runs.
4. **Three-Valued Evidence & Semantic Decoupling (ADR-004)**: Categorizes evidence as Demonstrated, Explicitly Absent, or Unestablished. Eliminates automatic zeroing for missing evidence and excludes uncalibrated semantic cosine scores from composite ranking.
5. **Application-Gated RAG & Role Spoofing Defense (ADR-005)**: Vector retrieval whitelists authorized resume IDs resolved from PostgreSQL. Database triggers prevent client chat sender-role spoofing.
6. **Lean Staging & Hardware-Calibrated Local AI (ADR-006)**: Standardized on host Ollama models (`qwen3:4b`, `llama3.2:1b`, `nomic-embed-text`) with low concurrency for Apple M2 (8GB RAM). Redis, Celery, MinIO, and ChromaDB are deferred until justified by application phases.

---

## Table of Decision Records

- [ADR-001: Multi-Tenant Identity, Active Context Derivation, and Candidate Privacy](#adr-001-multi-tenant-identity-active-context-derivation-and-candidate-privacy)
- [ADR-002: Dual-Layer Security Model: Hardened PostgreSQL RLS and Application Guards](#adr-002-dual-layer-security-model-hardened-postgresql-rls-and-application-guards)
- [ADR-003: Composite Constraint Integrity, Submitted Resume Immutability, and Deletion Protection](#adr-003-composite-constraint-integrity-submitted-resume-immutability-and-deletion-protection)
- [ADR-004: Three-Valued Evidence Scoring, Semantic Decoupling, and Objective Document Feedback](#adr-004-three-valued-evidence-scoring-semantic-decoupling-and-objective-document-feedback)
- [ADR-005: Application-Gated RAG Whitelisting, Prompt Sandboxing, and Role Anti-Spoofing](#adr-005-application-gated-rag-whitelisting-prompt-sandboxing-and-role-anti-spoofing)
- [ADR-006: Local-First Model Strategy and Staged Infrastructure Onboarding](#adr-006-local-first-model-strategy-and-staged-infrastructure-onboarding)

---

## ADR-001: Multi-Tenant Identity, Active Context Derivation, and Candidate Privacy

### 1. The Original Design Issue
The initial schema placed a single nullable `organization_id` foreign key directly on `users`, preventing recruiters from consulting for multiple organizations and conflating candidate identity with employer identity. Furthermore, V3 allowed active organization context to be accepted loosely without validating that `app.current_org_id` matched the user's verified active membership.

### 2. The Corrected Design
- `users` is strictly an identity and authentication table, decoupled from any single organization.
- `organization_memberships` establishes Many-to-Many relationships between `users` and `organizations` with roles (`OWNER`, `ADMIN`, `RECRUITER`, `VIEWER`) and statuses (`ACTIVE`, `SUSPENDED`, `REVOKED`).
- **Context Derivation**: Active organization context is derived exclusively from verified JWT authentication claims, never from client-supplied request bodies.
- **Dual-Context Helper**: `fn_has_active_org_membership(org_id, required_role)` strictly verifies that `app.current_user_id` is set, `app.current_org_id` equals `org_id`, membership is active, and the user's role satisfies the required hierarchy (`OWNER >= ADMIN >= RECRUITER >= VIEWER`).

### 3. Why the Correction Matters
- Prevents cross-tenant impersonation and client context spoofing.
- Preserves complete candidate privacy: a recruiter can only access candidate information through a submitted application to their organization's job.

### 4. How It Will Be Tested
- **Test 1.1 (Context Spoofing Test)**: Attempt a recruiter request with JWT claims for Org A while passing `organization_id = Org_B` in the request body; verify the request is rejected with `404 Not Found`.
- **Test 1.2 (Revoked Membership Test)**: Revoke a user's membership in Org A; verify that subsequent requests with existing JWTs fail active membership checks immediately.

---

## ADR-002: Dual-Layer Security Model: Hardened PostgreSQL RLS and Application Guards

### 1. The Original Design Issue
V3 omitted complete RLS on the `organizations` table, used insecure `search_path` defaults in security-definer functions, and lacked explicit separation between `talentlens_app` and the schema owner.

### 2. The Corrected Design
- **Complete Table Coverage**: RLS and `FORCE ROW LEVEL SECURITY` are enabled across all 13 tables, including `organizations`.
- **Hardened Security-Definer Functions**:
  - Owned by `talentlens_admin` (schema owner / migration user).
  - Explicit safe search path: `SET search_path = pg_catalog, public`.
  - Schema-qualified table references (`public.organization_memberships`).
  - Executable by `talentlens_app` (`NOBYPASSRLS`, non-superuser).
- **Parameterized Transaction Injection**: Uses PostgreSQL's native `set_config('app.current_user_id', :uid, true)` and `set_config('app.current_org_id', :oid, true)` inside active SQLAlchemy transactions.

### 3. Why the Correction Matters
- Prevents search path hijacking attacks against security-definer functions.
- Guarantees complete tenant isolation even if application code inadvertently omits `WHERE` clauses.

### 4. How It Will Be Tested
- **Test 2.1 (Search Path Hijacking Resistance)**: Create a malicious schema `public_attacker` with a forged `organization_memberships` table; execute `fn_has_active_org_membership`; verify it queries `public.organization_memberships` strictly.
- **Test 2.2 (Connection Pool Context Cleansing)**: Acquire a pooled connection, set tenant context, commit; re-acquire connection; assert `current_setting('app.current_org_id', true)` is empty.

---

## ADR-003: Composite Constraint Integrity, Submitted Resume Immutability, and Deletion Protection

### 1. The Original Design Issue
V3 used independent single-column foreign keys, which allowed cross-candidate resume submission (IDOR) and permitted historical screening results to point to an application from a different job. Furthermore, V3 used ordinary `<>` comparisons in triggers which fail on NULLs.

### 2. The Corrected Design
- **Composite Foreign Key (Anti-IDOR)**:
  `job_applications(submitted_resume_id, candidate_id) REFERENCES resumes(id, candidate_id)` structurally guarantees that a candidate can only submit their own resume.
- **Screening Result Referential Integrity**:
  `screening_results(job_application_id, job_id, organization_id, candidate_id, evaluated_resume_id)` references `job_applications` composite unique key, guaranteeing that screening results match the evaluated application and resume.
- **NULL-Safe Immutability Triggers**:
  Triggers use `IS DISTINCT FROM` to freeze all resume content, hashes, version identifiers, sections, and skills once submitted to any application.
- **Cascading Deletion Restrictions**:
  Jobs with submitted applications and resumes referenced by applications are protected with `ON DELETE RESTRICT`.

### 3. Why the Correction Matters
- Prevents tampering with submitted candidate resumes and screening audit trails.
- Guarantees compliance with statutory hiring retention requirements (EEOC / OFCCP).

### 4. How It Will Be Tested
- **Test 3.1 (Cross-Candidate Resume Submission)**: Candidate A attempts to submit Candidate B's `resume_id` on application creation; assert database foreign key constraint rejects the insert.
- **Test 3.2 (Submitted Resume Mutation Attempt)**: Execute `UPDATE resumes SET file_name = 'new.pdf' WHERE id = :submitted_id`; assert trigger raises an exception.

---

## ADR-004: Three-Valued Evidence Scoring, Semantic Decoupling, and Objective Document Feedback

### 1. The Original Design Issue
V3 divided demonstrated skills by total required skills, automatically penalizing candidates with low scores for unmentioned skills despite documentation stating unmentioned skills are not deficiencies. Furthermore, V3 included uncalibrated semantic cosine similarity in the ranking score.

### 2. The Corrected Design
- **Three-Valued Evidence Ontology**:
  - **Demonstrated**: Verifiable evidence with verbatim citations ($+1.0$).
  - **Explicitly Absent**: Document explicitly states non-familiarity ($0.0$).
  - **Unestablished**: Requirement is unmentioned. Increments Uncertainty ($U$).
- **Evidence Coverage ($C_{evidence}$)**:
  $$C_{evidence} = \frac{\sum_{i \in \text{Demonstrated}} w_i + \sum_{k \in \text{Explicitly Absent}} w_k}{\sum_{j \in \text{Required}} w_j}$$
  If $C_{evidence} < 0.30$, score is flagged as `INSUFFICIENT_EVIDENCE` and routed for human review.
- **Semantic Similarity Decoupled from Ranking**:
  Cosine similarity is excluded from composite fit ranking until empirical benchmark datasets support calibration. It is reported strictly as an informational metric.
- **Experience Alignment**:
  Deduplicates calendar months across concurrent roles; categorizes internships/academic projects; flags missing dates as `UNVERIFIED` without arbitrary zeroing.

### 3. Why the Correction Matters
- Eliminates algorithmic bias that mistakes missing resume text for proven incompetence.
- Adheres to ethical hiring standards by keeping decisions explainable and human-supervised.

### 4. How It Will Be Tested
- **Test 4.1 (Insufficient Evidence Flagging)**: Evaluate a 1-page resume against a 15-skill senior JD where only 2 skills are mentioned; verify status is `INSUFFICIENT_EVIDENCE` and candidate is not assigned an arbitrary numeric score.
- **Test 4.2 (Experience Month Deduplication)**: Candidate with two overlapping 1-year roles (Jan 2023 - Dec 2023); verify experience engine counts 12 calendar months, not 24.

---

## ADR-005: Application-Gated RAG Whitelisting, Prompt Sandboxing, and Role Anti-Spoofing

### 1. The Original Design Issue
V3 assigned resume vector chunks exclusively to one tenant or job in ChromaDB, which breaks when a candidate applies to multiple companies with the same resume. Furthermore, V3 allowed clients to insert chat messages with `sender_role = 'ASSISTANT'`.

### 2. The Corrected Design
- **Application-Scoped RAG Pipeline**:
  Vector embeddings are candidate-owned. When a recruiter queries their assistant:
  1. Backend queries PostgreSQL for authorized `submitted_resume_id`s tied to that job.
  2. Vector store query injects mandatory filter: `{"resume_id": {"$in": authorized_resume_ids}}`.
  3. Post-retrieval verification asserts all retrieved chunks belong to the authorized whitelist.
- **Chat Role Anti-Spoofing**:
  Database trigger on `rag_chat_messages` enforces that client-inserted messages must have `sender_role = 'USER'`.
- **Prompt Sandboxing**:
  Untrusted resume text is wrapped in randomized delimiter tags (`<untrusted_candidate_document hash="...">...</untrusted_candidate_document>`) with strict system prompt precedence.

### 3. Why the Correction Matters
- Prevents candidates from reading other applicants' data or injecting malicious assistant turns.
- Eliminates cross-tenant data leakage in conversational RAG assistants.

### 4. How It Will Be Tested
- **Test 5.1 (Chat Sender Role Spoofing)**: Client attempts `INSERT INTO rag_chat_messages (sender_role, ...) VALUES ('ASSISTANT', ...)`; verify trigger aborts insertion.
- **Test 5.2 (Recruiter Cross-Requisition RAG)**: Recruiter queries assistant about a candidate who applied to Job A; verify the assistant cannot access that candidate when querying under Job B.

---

## ADR-006: Local-First Model Strategy and Staged Infrastructure Onboarding

### 1. The Original Design Issue
V3 included Redis in Phase 1 before any background queues existed, made unverified "100% offline" claims, and lacked hardware-specific calibration for developer machines.

### 2. The Corrected Design
- **Local Model Fleet**:
  - `TALENTLENS_LLM_MODEL=qwen3:4b`
  - `TALENTLENS_FALLBACK_MODEL=llama3.2:1b`
  - `TALENTLENS_EMBEDDING_MODEL=nomic-embed-text`
  - Setup command: `ollama pull nomic-embed-text && ollama pull qwen3:4b && ollama pull llama3.2:1b`.
  - Accurate statement: *"Local model inference without paid cloud API keys"*.
- **Hardware Calibration (Apple M2, 8GB RAM)**:
  Inference concurrency is capped at 1 generation at a time to prevent unified memory swapping on 8GB machines.
- **Lean Phase 1 Stack**:
  Phase 1 runs solely on **PostgreSQL 16, FastAPI, React 18, and Host Ollama**. Redis and Celery are introduced in Phase 4 for bulk screening; ChromaDB is introduced in Phase 5 for RAG.

### 3. Why the Correction Matters
- Reduces developer onboarding friction and eliminates unnecessary memory consumption on 8GB workstations.
- Ensures fast, predictable execution without cloud subscription costs.

### 4. How It Will Be Tested
- **Test 6.1 (Local Model Inference)**: Script executes a prompt against host Ollama `qwen3:4b` and asserts response completes in $< 3$ seconds on Apple M2 hardware.
- **Test 6.2 (Phase 1 Boot Time)**: Assert `docker-compose -f docker-compose.dev.yml up` completes in $< 10$ seconds without Redis.

---

## ADR-007: Candidate Resume Intelligence & Career Guidance Architecture (Milestone 7)

### Context
Candidates need actionable feedback on how their resumes communicate technical competencies and how they can tailor their resumes toward specific roles. However, this feature must not conflict with recruitment screening, create recruiter bias, or alter evaluation scores.

### Decision
1. **Complete Decoupling from M6 Screening Engine**:
   - M7 Career Guidance is strictly private to the candidate.
   - It **never** alters M6 screening scores, matching algorithms, or recruiter leaderboard ranks.
   - Recruiters have zero access to candidate-generated analyses.
2. **Hybrid Architecture**:
   - Pure Python deterministic static checks evaluate text length, standard section presence, direct contact details, missing descriptions, and quantitative metrics without LLM cost or hallucination risk.
   - Local Ollama LLM (`qwen3:4b` primary, `llama3.2:1b` fallback) provides qualitative technical evaluation, contextual skill identification, and actionable suggestions.
3. **Deterministic Fallback Resilience**:
   - If Ollama is unavailable, times out, or returns invalid structure, the system generates a pure Python rule-based advisory payload, stores status as `FAILED`, and allows controlled candidate retries.
4. **Safety and Prompt Injection Defense**:
   - Resume content is strictly fenced as untrusted input.
   - No protected attributes, age, gender, or pedigree biases are evaluated.
   - No numerical scores or grades are assigned.

---

## ADR-008: Candidate AI Career Assistant Architecture (Milestone 8)

### Context
Candidates need an interactive conversational mentor to understand their profile, explore career transition paths, generate learning roadmaps, and practice technical interview questions based strictly on their actual uploaded experience. The feature must be strictly private to the candidate, resilient against model latency/failure, and independent of recruiter screening algorithms.

### Decision
1. **Lightweight Section-Aware Retrieval (No ChromaDB / Vector DB Required)**:
   - For interactive conversational career mentoring, candidate resume data is already parsed into structured sections (`skills`, `projects`, `experience`, `education`, `summary`).
   - Keyword-based intent classification maps queries directly to relevant sections, bounding prompt length to $< 1,500$ words and achieving $< 4$ second generation times on Apple M2 hardware without the latency and memory overhead of an external vector database.
2. **Strict Privacy and Candidate-Only Access**:
   - Recruiters and organization members have zero access to candidate career conversations (`GET` requests by recruiters return `404 Not Found`).
   - Conversations are private to the candidate and strictly isolated from the M6 candidate screening engine and ranking leaderboards.
3. **Structured Provenance Tracking**:
   - Rather than duplicating raw resume text into message rows, each assistant message stores rich provenance metadata (`resume_id`, `resume_sha256`, `m7_analysis_id`, `retrieved_sections`, `evidence_snippets`, and `is_fallback`).
4. **Deterministic Advisory Fallback**:
   - In case of local model timeout or service unreachability, the assistant gracefully provides a rule-based advisory response covering STAR outlines, 30-day learning roadmaps, and project communication techniques directly derived from retrieved records.
