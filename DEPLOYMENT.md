# TalentLens: Production & Staging Deployment Guide

**Document Version**: 1.0  
**Target Environment**: Linux / macOS (Production & Staging)  
**Stack**: FastAPI (Python 3.13), PostgreSQL 17, Vite + React 18, Local / Host Ollama

---

## 1. Architecture Overview

TalentLens operates as a hardened Modular Monolith:
- **Backend**: Asynchronous FastAPI service running under `uvicorn` (or behind Nginx / Gunicorn with `UvicornWorker`).
- **Database**: PostgreSQL 17 with UUID and JSONB extensions, managed via Alembic migrations.
- **Frontend**: Static React 18 SPA built with Vite and served by Nginx, Cloudflare Pages, AWS S3 / CloudFront, or any standard HTTP web server.
- **AI Inference**: Host or sidecar Ollama instance (`qwen3:4b` primary, `llama3.2:1b` fallback) with automatic deterministic fallback if Ollama is unreachable.
- **File Storage**: Persistent filesystem storage for candidate PDF resumes with sha256 hashing and directory traversal protection.

---

## 2. Infrastructure Prerequisites

| Component | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **CPU** | 2 vCPUs | 4+ vCPUs (Apple Silicon or modern x86_64) |
| **RAM** | 8 GB Unified / System RAM | 16 GB RAM (for concurrent local AI) |
| **Disk** | 20 GB SSD | 50+ GB SSD (for model weights & resumes) |
| **Python** | Python 3.11+ (Tested on 3.13) | Python 3.13 |
| **Node.js** | Node 18+ (Tested on 20) | Node 20 LTS |
| **Database** | PostgreSQL 16+ | PostgreSQL 17 |
| **Ollama** | Host Ollama 0.3+ | Host Ollama 0.5+ |

---

## 3. Environment Configuration

Copy `.env.example` to `.env` in the backend root:

```bash
cp .env.example backend/.env
```

### Critical Environment Variables

| Variable | Description | Example / Requirement |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Runtime mode: `development`, `staging`, `production` | `production` |
| `SECRET_KEY` | High-entropy signing key (32+ chars) | `openssl rand -hex 32` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `DOCS_ENABLED` | Toggle Swagger UI / ReDoc | `false` in production |
| `CORS_ORIGINS` | Permitted browser origins | `["https://app.talentlens.com"]` |
| `UPLOAD_DIR` | Absolute path for stored PDF resumes | `/var/data/talentlens/resumes` |
| `MAX_UPLOAD_SIZE_BYTES` | Maximum PDF file upload size | `5242880` (5 MB) |
| `OLLAMA_BASE_URL` | Ollama HTTP endpoint | `http://127.0.0.1:11434` |
| `RATE_LIMIT_ENABLED` | Toggle in-memory rate limiting | `true` |

> [!CAUTION]
> If `ENVIRONMENT=production`, the application will **fail startup immediately** if `SECRET_KEY` uses the default development fallback or has fewer than 32 characters.

---

## 4. Database Setup & Migrations

1. **Create PostgreSQL Database**:
   ```sql
   CREATE DATABASE talentlens_production;
   CREATE USER talentlens_user WITH ENCRYPTED PASSWORD 'your_strong_password';
   GRANT ALL PRIVILEGES ON DATABASE talentlens_production TO talentlens_user;
   ```

2. **Run Migrations to Head**:
   ```bash
   cd backend
   source venv/bin/activate
   alembic upgrade head
   ```

3. **Verify Migration Status**:
   ```bash
   alembic current
   ```

---

## 5. Local Ollama Model Setup

If running local inference:
```bash
ollama pull qwen3:4b
ollama pull llama3.2:1b
```
Verify the daemon is reachable:
```bash
curl http://localhost:11434/api/tags
```

> [!NOTE]
> If Ollama is offline or experiences transient timeouts, TalentLens will automatically activate its rule-based deterministic fallback engine for all M6, M7, M8, and M9 workflows. Core application features (auth, job publishing, applications) will remain 100% operational.

---

## 6. Backend Production Service Setup

### Running with Systemd (Linux)

Create `/etc/systemd/system/talentlens-api.service`:

```ini
[Unit]
Description=TalentLens API Service
After=network.target postgresql.service

[Service]
Type=simple
User=talentlens
WorkingDirectory=/var/www/talentlens/backend
EnvironmentFile=/var/www/talentlens/backend/.env
ExecStart=/var/www/talentlens/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable talentlens-api
sudo systemctl start talentlens-api
```

---

## 7. Frontend Production Build & Hosting

1. **Configure Environment**:
   Create `frontend/react-ts/.env.production`:
   ```env
   VITE_API_URL=https://api.talentlens.com
   ```

2. **Build Production Assets**:
   ```bash
   cd frontend/react-ts
   npm ci
   npm run build
   ```

3. **Serve with Nginx**:
   ```nginx
   server {
       listen 80;
       server_name app.talentlens.com;
       root /var/www/talentlens/frontend/react-ts/dist;
       index index.html;

       location / {
           try_files $uri $uri/ /index.html;
       }

       # Proxy API requests
       location /api/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

---

## 8. Verification & Health Probing

After starting backend and frontend:

1. **Check Liveness**:
   ```bash
   curl -i http://localhost:8000/health/live
   # HTTP/1.1 200 OK
   # {"status":"alive","timestamp":"...","environment":"production"}
   ```

2. **Check Readiness**:
   ```bash
   curl -i http://localhost:8000/health/ready
   # HTTP/1.1 200 OK
   # {"status":"ready","timestamp":"...","database":"connected","ai_service":"available"}
   ```
