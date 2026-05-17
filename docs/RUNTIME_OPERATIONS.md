# BarkMind — Runtime Operations

**Date:** 2026-05-17

---

## Process Model

BarkMind runs as two independent processes:

| Process | Command | Port | PID File |
|---|---|---|---|
| Backend | `uvicorn app.main:app` | 8108 | `runtime/backend.pid` |
| Frontend | `npm run start` | 3008 | `runtime/frontend.pid` |

Processes are started with `setsid` + `disown` — they survive terminal closure.

---

## Lifecycle Commands

```bash
./start.sh    # Start both backend and frontend
./stop.sh     # Stop both (graceful, then SIGKILL)
./restart.sh  # stop.sh + 2s pause + start.sh
./status.sh   # Show PID, port, and health status
```

---

## Health Checks

**Backend:**
```bash
curl http://127.0.0.1:8108/health
# → {"status": "ok", "service": "barkmind", "version": "1.0.0"}
```

**Governance status (for Aegis):**
```bash
curl http://127.0.0.1:8108/governance/status
```

**Frontend:**
```bash
curl -o /dev/null -w "%{http_code}" http://127.0.0.1:3008
# → 200
```

---

## Log Management

```bash
# Live backend log
tail -f logs/backend.log

# Live frontend log
tail -f logs/frontend.log

# Last 100 backend log lines
tail -100 logs/backend.log

# Filter errors only
grep -E "ERROR|CRITICAL" logs/backend.log

# Filter media processing events
grep "barkmind.media" logs/backend.log
```

Logs rotate on each `start.sh` call (appended, not replaced).

---

## Database Operations

```bash
# Connect
psql "postgresql://barkmind_user:barkmind_dev_password@127.0.0.1:5432/barkmind"

# Check migration status
cd backend && alembic current

# Run pending migrations
cd backend && alembic upgrade head

# View migration history
cd backend && alembic history

# Rollback one migration
cd backend && alembic downgrade -1
```

---

## Media Storage

```
media/cases/{case_id}/
  original/    ← uploaded files
  thumbnails/  ← sm/md/lg JPEG thumbnails
  derived/     ← future processed variants
  frames/      ← future AI frame extracts
```

```bash
# Check disk usage
du -sh media/

# Count files per directory
find media/ -type f | wc -l

# Run orphan cleanup (dry run)
cd backend && python -m app.scripts.cleanup_media --verbose

# Run orphan cleanup (delete)
cd backend && python -m app.scripts.cleanup_media --delete
```

---

## Governance Operations

```bash
BASE=http://127.0.0.1:8108

# Platform metrics
curl $BASE/governance/metrics

# Audit trail (admin)
curl -H "Authorization: Bearer $TOKEN" "$BASE/audit?limit=20"

# Stale reviews
curl -H "Authorization: Bearer $TOKEN" "$BASE/telemetry/ops"

# Event stream replay
curl -H "Authorization: Bearer $TOKEN" "$BASE/telemetry/events?since=2026-05-17T00:00:00Z"
```

---

## Data Exports

```bash
TOKEN="your-admin-token"

# Export all cases as NDJSON
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8108/exports/cases?format=ndjson" \
  -o cases_export.ndjson

# Export annotations as JSON
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8108/exports/annotations?format=json" \
  -o annotations_export.json

# Take a dataset snapshot
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8108/dataset/snapshot?name=my-snapshot&version_tag=v1.0"
```

---

## Promoting Users

```bash
# Promote to expert
psql "postgresql://barkmind_user:barkmind_dev_password@127.0.0.1:5432/barkmind" \
  -c "UPDATE users SET role='expert' WHERE username='username';"

# Promote to admin
psql "postgresql://barkmind_user:barkmind_dev_password@127.0.0.1:5432/barkmind" \
  -c "UPDATE users SET role='admin' WHERE username='username';"
```

---

## Reset for Clean Testing

```bash
# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS barkmind;"
sudo -u postgres psql -c "CREATE DATABASE barkmind OWNER barkmind_user;"
sudo -u postgres psql -d barkmind -c "GRANT ALL ON SCHEMA public TO barkmind_user;"

# Re-run all migrations + seed
cd backend && alembic upgrade head

# Tags and taxonomy re-seed automatically on next startup
```

---

## Troubleshooting

**Backend won't start:**
```bash
tail -50 logs/backend.log
# Check for: DB connection failed, port in use, missing .env
```

**Port conflicts:**
```bash
lsof -i:8108   # Check backend port
lsof -i:3008   # Check frontend port
# Use kill PID to remove occupant if it's a stale process
```

**Frontend shows stale data:**
```bash
# Hard refresh in browser: Ctrl+Shift+R
# Or rebuild: cd frontend && npm run build
```

**Thumbnails not generating:**
```bash
which ffmpeg         # Check ffmpeg available
grep "barkmind.media" logs/backend.log | tail -20
# Check for: processing_status=failed in response
```

**Migration fails:**
```bash
cd backend && alembic current  # See current state
cd backend && alembic history  # See full chain
# If corrupted: restore DB from backup, re-run from clean
```
