# TalentLens MVP: Repository Audit & Component Reusability Analysis

**Document Version**: 1.0  
**Status**: Completed Pre-Implementation Audit  
**Target Platform**: TalentLens MVP — Multi-Tenant AI Recruitment & Career Intelligence Platform  
**Target Repository**: `resume-rag`  

---

## 1. Executive Summary

This audit evaluates the ground-truth state of the `resume-rag` codebase to plan a practical, rapid MVP implementation of **TalentLens** supporting multiple organizations from day one.

The existing codebase is an early proof-of-concept (PoC) designed for single-user keyword matching against a local vector database. While it lacks relational persistence, authentication, multi-tenancy, and proper error handling, it contains several functional assets that can be repurposed to accelerate MVP delivery.

### Key Audit Findings:
- **Environment Ground Truth**: The developer machine is an **Apple M2 (8GB RAM) running macOS**. PostgreSQL 17 is already installed and running locally via Postgres.app on port `5432`. Ollama is running on port `11434` with `qwen3:4b`, `llama3.2:1b`, and `nomic-embed-text:latest` pre-installed. **Docker is not installed** on the host machine.
- **Frontend Ground Truth**: Located in `frontend/react-ts/`. It is a Vite 5.4 + React 18.3 + Tailwind CSS v4 project. It currently renders a single monolithic component (`App.tsx`) with a textarea and card rendering.
- **Backend Ground Truth**: Located in `backend/`. Runs FastAPI with a single `POST /match` route in `main.py`. It has zero database persistence (relies on flat JSON files in `candidate_profiles/` and a local ChromaDB folder).
- **Critical Defects**: Semantic retrieval in `batch_matcher.py` fails due to an undefined variable (`temporary_query_embedding`), silently dropping to heuristic string matching. Index rebuilding in `build_resume_index.py` deletes the vector database directory via `shutil.rmtree`.

---

## 2. In-Depth Inspection of Existing Repository Components

### 2.1 Backend Structure & Dependencies

```text
backend/
├── candidate_profiles/         # 6 mock candidate JSON profiles (cand_001.json - cand_006.json)
├── chroma_db/                  # SQLite + Chroma binary index files
├── data/
│   ├── jds/                    # Sample JD JSON (jd.json)
│   └── resumes/                # 6 pre-compiled PDF resumes (cand_001.pdf - cand_006.pdf)
├── models/
│   └── schemas.py              # 0 bytes (Empty file)
├── services/
│   ├── batch_matcher.py        # Core matching logic, Ollama prompts, heuristic fallback
│   ├── build_jds_index.py      # Standalone Chroma JD indexing script
│   └── build_resume_index.py   # Destructive resume indexing script (shutil.rmtree)
├── test/
│   ├── generate_mock.py        # ReportLab PDF resume generator from JSON profiles
│   ├── jd_parser.py            # PDF text extraction and Ollama JSON extraction test
│   └── query_resumes.py        # LlamaIndex query engine demonstration script
├── tests/
│   └── test_batch_matcher.py   # Broken unit test (parameter signature mismatch)
├── main.py                     # FastAPI app with GET / and POST /match
└── requirements.txt            # Unpinned dependencies (llama-index, chromadb, pydantic, pypdf)
```

#### Detailed Source File Review:
1. **`backend/main.py` (54 LOC)**:
   - Sets up FastAPI and permissive CORS (`localhost:5173` through `5175`).
   - Declares `JobDescription(BaseModel)` with a single field: `raw_text: str`.
   - `POST /match` executes `run_candidate_matcher(raw_text=jd.raw_text, ...)` synchronously in the event loop.
   - Errors are caught with a broad `except Exception:` returning HTTP 500 JSON.
2. **`backend/services/batch_matcher.py` (277 LOC)**:
   - `extract_skills_from_raw_jd`: Prompts Ollama with prompt template. **Defect**: Calls module `ollama(...)` directly as a callable with invalid argument `formal='json'`, raising `TypeError` and triggering a fallback that splits raw text by commas.
   - `_skill_matches`: Bidirectional substring normalization (`s_norm in c_norm or c_norm in s_norm`), causing severe false positives (e.g., "c" matches "react", "go" matches "django").
   - `run_candidate_matcher`: Attempts vector retrieval from Chroma, but line 185 uses `query_embeddings=[temporary_query_embedding]`. Because `temporary_query_embedding` is undefined, this raises `NameError`, silently falling back to `_heuristic_rank_candidates`.
   - `_heuristic_rank_candidates`: Scores candidates using `len(matched_skills) * 20` capped at 99. Completely ignores experience depth.
3. **`backend/test/generate_mock.py` (69 LOC)**:
   - Uses `reportlab` to render well-structured PDF resumes from candidate JSON profiles. Functional, clean, and highly reusable for test fixture creation.
4. **`backend/test/jd_parser.py` (76 LOC)**:
   - Uses `pypdf.PdfReader` to extract text from PDFs and prompts Ollama for structured JSON.
   - **Defect**: Main block points `TARGET_JD` to a `.json` file (`../data/jds/jd.json`) rather than a `.pdf`, causing a PDF read crash.

### 2.2 Frontend Structure & Dependencies

```text
frontend/react-ts/
├── src/
│   ├── assets/                 # SVGs and hero images
│   ├── App.css                 # Single line: @import "tailwindcss";
│   ├── App.tsx                 # Monolithic React component (142 LOC)
│   ├── index.css               # Base CSS variables and typography
│   └── main.tsx                # React DOM createRoot entrypoint
├── package.json                # React 18.3.1, Vite 5.4.10, @tailwindcss/vite 4.3.2
├── tsconfig.json               # TypeScript project references
└── vite.config.ts              # Vite config with React and Tailwind plugins
```

#### Detailed Frontend Review:
- **`App.tsx`**: Contains all UI logic in a single file:
  - Input workspace on the left: text area for pasting raw JD text and a "Match Candidates" button.
  - Live screening results on the right: renders candidate cards showing score percentage, matched skills, missing skills, and AI reasoning text.
  - State management uses local `useState` hooks. No routing, no authentication, no user role differentiation.
  - Modern styling using Tailwind CSS with dark-mode slate theme.

---

## 3. Component Reusability Classification

| Component / Artifact | Current Location | Classification | MVP Disposition & Action Plan |
| :--- | :--- | :--- | :--- |
| **PDF Resume Generator** | `backend/test/generate_mock.py` | **Reusable without changes** | Relocate to `backend/tests/fixtures/resume_factory.py`. Use to generate synthetic resumes for automated tests and demo seed data. |
| **Candidate Mock Profiles** | `backend/candidate_profiles/*.json` | **Reusable without changes** | Ingest as initial database seed data for candidates in `scripts/seed_mvp_data.py`. |
| **Sample Job Descriptions** | `backend/data/jds/jd.json` | **Reusable without changes** | Ingest as initial seed requisitions for test organizations. |
| **Tailwind & Vite Setup** | `frontend/react-ts/` | **Reusable without changes** | Keep Vite bundler, React 18.3, and Tailwind CSS v4 styling configuration intact. |
| **Candidate Card UI Design** | `frontend/react-ts/src/App.tsx` | **Reusable with modifications** | Extract candidate match cards into a modular component `CandidateResultCard.tsx`. |
| **Ollama Extraction Prompt** | `backend/services/batch_matcher.py` | **Reusable with modifications** | Fix syntax error: call `ollama.generate(model=..., prompt=..., format='json')`. Target local `qwen3:4b`. |
| **Skill Normalization Logic** | `backend/services/batch_matcher.py` | **Reusable with modifications** | Replace loose bidirectional substring check with exact token equality on canonical skill tags. |
| **PDF Text Extraction** | `backend/test/jd_parser.py` | **Reusable with modifications** | Replace `pypdf` with `pymupdf` (fitz) or `pdfplumber` for superior layout and multi-column parsing. |
| **Batch Matcher Retrieval** | `backend/services/batch_matcher.py` | **Broken / Replace** | Discard `temporary_query_embedding` and Chroma vector retrieval for MVP. Use deterministic database queries. |
| **Heuristic Scoring ($N \times 20$)** | `backend/services/batch_matcher.py` | **Broken / Replace** | Replace with multi-factor deterministic scoring: canonical required skills, preferred skills, and experience check. |
| **Vector DB Indexer** | `backend/services/build_resume_index.py`| **Broken / Replace** | Discard `shutil.rmtree` destructive wiping. |
| **FastAPI Monolith Entrypoint** | `backend/main.py` | **Broken / Replace** | Refactor into modular routers: `auth`, `candidates`, `recruiters`, `jobs`, `applications`. |
| **ChromaDB / LlamaIndex** | `backend/chroma_db/`, `requirements.txt` | **Not needed for MVP** | **Omit from MVP**. Unnecessary complexity. Rely on PostgreSQL and direct Python scoring logic. |
| **Redis / Celery / MinIO** | N/A (Architecture proposals) | **Not needed for MVP** | **Omit from MVP**. Store files on local filesystem; execute parsing synchronously or via FastAPI `BackgroundTasks`. |

---

## 4. Technical Blockers & Environmental Considerations

### 4.1 Missing Backend Dependencies for MVP
The existing `backend/requirements.txt` lacks critical production packages:
- **Persistence**: Missing `sqlalchemy` (ORM), `psycopg2-binary` or `asyncpg` (PostgreSQL driver), `alembic` (database migrations).
- **Authentication**: Missing `pyjwt` (JWT generation/decoding), `passlib[bcrypt]` (password hashing), `python-multipart` (file uploads).
- **PDF Extraction**: Missing `pymupdf` (fitz).
- **Environment**: Missing `pydantic-settings` (typed environment configuration).

### 4.2 Incompatible Frontend-Backend Interface
- Currently, the frontend assumes a single synchronous call:
  `POST /match` with payload `{"raw_text": "..."}` returning `{"candidate": [...]}`.
- The MVP requires an authenticated session:
  - Candidates: login $\rightarrow$ upload resume $\rightarrow$ browse published jobs $\rightarrow$ click "Apply".
  - Recruiters: login $\rightarrow$ select/create organization $\rightarrow$ post job $\rightarrow$ view applicant list $\rightarrow$ click "Screen Applicants".
- The frontend must introduce simple tab-based or route-based navigation (e.g., React Router or state-driven views) to separate Candidate and Recruiter portals.

### 4.3 Database Environment & Tooling
- **Verified Environment**: PostgreSQL 17 is already running on `localhost:5432` via Postgres.app. Docker is not installed on the host.
- **MVP Adaptation**: Rather than requiring Docker, the MVP backend will connect directly to the local Postgres.app instance using a local database (`talentlens_mvp`). This eliminates Docker installation friction on the Apple M2 machine.

### 4.4 Local AI Inference Constraints
- Ollama is running natively on the host with `qwen3:4b` and `llama3.2:1b`.
- On an Apple M2 with 8GB RAM, concurrent LLM inferences will cause memory pressure. The MVP screening engine will parse resumes sequentially or cache parsed profile JSON in PostgreSQL so screening runs compute scores instantly via deterministic Python matching without repeated LLM calls.
