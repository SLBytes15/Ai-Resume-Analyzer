# TalentLens: Operations, Observability & Backup Runbook

**Document Version**: 1.0  
**Target Audience**: DevOps Engineers, Site Reliability Engineers, Platform Administrators  
**Scope**: Ongoing operations, health monitoring, database & storage backup/recovery, and incident response.

---

## 1. Health Monitoring & Observability

### 1.1 Probes & Endpoints

| Probe | Path | Expected Status | Description |
| :--- | :--- | :--- | :--- |
| **Liveness** | `GET /health/live` | `200 OK` | Verifies web process is alive and accepting event loop connections |
| **Readiness** | `GET /health/ready` | `200 OK` / `503 Service Unavailable` | Pings PostgreSQL (`SELECT 1`). Returns 503 if database disconnected |
| **Legacy / Basic** | `GET /health` | `200 OK` | Backward-compatible status endpoint |

### 1.2 Structured Logging & Request Correlation

Every HTTP request processes through `request_logging_middleware`:
- Emits single-line structured JSON logs with `timestamp`, `level`, `logger`, `message`, and `request_id`.
- Propagates `X-Request-ID` in request headers and responses.
- To trace an incident across logs:
  ```bash
  # Filter logs for a specific request ID
  journalctl -u talentlens-api | grep "req_9b1deb4d-3b7d"
  ```

---

## 2. Backup & Disaster Recovery Procedures

### 2.1 Database Backup (PostgreSQL)

Perform daily automated dumps with transaction logs:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/talentlens/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Perform compressed custom-format pg_dump
pg_dump -U talentlens_user -h localhost -F c -b -v -f "$BACKUP_DIR/talentlens_$DATE.dump" talentlens_production

# Retain backups for 30 days
find "$BACKUP_DIR" -type f -name "*.dump" -mtime +30 -delete
```

### 2.2 Resume File Storage Backup

Candidate resumes reside on disk under `UPLOAD_DIR` (e.g., `/var/data/talentlens/resumes`).
Backup with `rsync` or snapshot storage:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/talentlens/resumes"
mkdir -p "$BACKUP_DIR"

rsync -avz --delete /var/data/talentlens/resumes/ "$BACKUP_DIR/current/"
```

### 2.3 Restoration Procedure

1. **Restore PostgreSQL Database**:
   ```bash
   # Drop existing connections and restore
   pg_restore -U talentlens_user -h localhost -d talentlens_production -v --clean --if-exists "$BACKUP_DIR/talentlens_20261123_120000.dump"
   ```

2. **Restore Filesystem Storage**:
   ```bash
   rsync -avz "$BACKUP_DIR/current/" /var/data/talentlens/resumes/
   ```

3. **Verify Integrity**:
   Run the test suite or verify candidate resume hashes against stored files:
   ```bash
   python -c "
   import asyncio
   from app.core.database import async_session_maker
   from app.models.candidate import Resume
   from sqlalchemy import select
   # Verify resume files exist on disk
   "
   ```

---

## 3. Incident Response & Troubleshooting

### 3.1 Database Disconnection (Readiness Probe 503)
- **Symptom**: `/health/ready` returns `HTTP 503 Service Unavailable`.
- **Action**:
  1. Check PostgreSQL service: `sudo systemctl status postgresql`
  2. Verify connection string in `.env` (`DATABASE_URL`).
  3. Inspect PostgreSQL logs: `/var/log/postgresql/`

### 3.2 Ollama Outage or Degradation
- **Symptom**: `/health/ready` reports `"ai_service": "offline"`.
- **Behavior**: Core non-AI endpoints continue operating normally. Screening and AI assistant endpoints automatically switch to deterministic rule-based fallback mode.
- **Action**:
  1. Restart Ollama daemon: `sudo systemctl restart ollama` or `ollama serve`.
  2. Verify models: `ollama list` (ensure `qwen3:4b` and `llama3.2:1b` are loaded).

### 3.3 Rate Limit Triggers (HTTP 429)
- **Symptom**: User receives `HTTP 429 Too Many Requests`.
- **Action**: Verify client IP isn't undergoing a credential brute force. If legitimate bulk operations require higher quotas, adjust `RATE_LIMIT_AUTH_PER_MINUTE`, `RATE_LIMIT_AI_PER_MINUTE`, or `RATE_LIMIT_UPLOAD_PER_HOUR` in `.env` and reload the service.

---

## 4. Rollback Procedures

If a deployment fails:
1. Revert backend code: `git checkout <previous_commit_tag>`
2. Downgrade database if required:
   ```bash
   cd backend
   alembic downgrade -1
   ```
3. Restart application service: `sudo systemctl restart talentlens-api`
