# BarkMind — Deployment Guide

**Date:** 2026-05-17  
**Environment:** Local VM (vmi3002990)

---

## Ports

| Component | Port | Notes |
|---|---|---|
| BarkMind backend | **8108** | Canonical — Aegis Lite owns 8107 |
| BarkMind frontend | **3008** | Canonical — Aegis Lite owns 3007 |
| Aegis Lite backend | 8107 | Do not touch |
| Aegis Lite frontend | 3007 | Do not touch |

---

## Prerequisites

```bash
# Python 3.12+
python3 --version

# uvicorn (should be installed system-wide or in venv)
uvicorn --version

# PostgreSQL running
pg_isready -h 127.0.0.1 -p 5432

# ffmpeg (for video thumbnails)
ffmpeg -version
```

---

## First-Time Setup

### 1. Copy and configure .env

```bash
cp .env.example .env
# Edit .env — required:
#   DATABASE_URL=postgresql+asyncpg://barkmind_user:PASSWORD@127.0.0.1:5432/barkmind
#   JWT_SECRET=<long random string>
```

### 2. Create PostgreSQL database

```bash
sudo -u postgres psql <<SQL
CREATE USER barkmind_user WITH PASSWORD 'yourpassword';
CREATE DATABASE barkmind OWNER barkmind_user;
GRANT ALL PRIVILEGES ON DATABASE barkmind TO barkmind_user;
\connect barkmind
GRANT ALL ON SCHEMA public TO barkmind_user;
SQL
```

### 3. Run migrations

```bash
cd backend
alembic upgrade head
cd ..
```

### 4. Build frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

---

## Starting BarkMind

```bash
./start.sh
```

`start.sh` will:
1. Validate dependencies (python3, uvicorn)
2. Check port availability (:8108, :3008)
3. Clean up stale PID files
4. Start backend (uvicorn on :8108)
5. Wait for backend health (30s timeout)
6. Start frontend (Next.js on :3008, if built)
7. Attempt Aegis registration
8. Print summary with startup time

---

## Stopping BarkMind

```bash
./stop.sh
```

Sends SIGTERM, waits 10s for graceful shutdown, SIGKILL if needed.
Falls back to port-based kill if no PID file exists.

---

## Restart

```bash
./restart.sh
```

Equivalent to `./stop.sh && sleep 2 && ./start.sh`.

---

## Status Check

```bash
./status.sh
```

Shows:
- PID status (running/stale/not started)
- Port occupancy
- Backend health check result
- Log file locations
- Endpoint URLs

---

## Development Mode

For development with hot-reload:

```bash
# Backend (hot-reload)
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8108 --reload --log-level debug

# Frontend (dev server)
cd frontend
npm run dev  # runs on :3008
```

---

## Cloudflare Tunnel

Add to `~/.cloudflared/config.yml` (reselleros tunnel):

```yaml
# BarkMind
- hostname: barkmind-api.jesseboudreau.com
  service: http://127.0.0.1:8108

- hostname: barkmind.jesseboudreau.com
  service: http://127.0.0.1:3008
```

Then update frontend env:
```
NEXT_PUBLIC_API_URL=https://barkmind-api.jesseboudreau.com
```

And rebuild frontend:
```bash
cd frontend && npm run build
```

---

## Environment Variables

| Variable | Default | Required |
|---|---|---|
| `BACKEND_PORT` | 8108 | Yes |
| `FRONTEND_PORT` | 3008 | Yes |
| `DATABASE_URL` | (none) | Yes |
| `JWT_SECRET` | (none) | Yes — must be random |
| `MEDIA_ROOT` | `./media` | No |
| `MEDIA_BACKEND` | `local` | No |
| `LOG_LEVEL` | `INFO` | No |
| `AEGIS_BASE_URL` | `http://127.0.0.1:8102` | No |
| `OPENCLAW_BASE_URL` | `http://127.0.0.1:18789` | No |
| `SERVICE_API_KEY` | (default) | Change in production |

---

## Logs

```bash
# Backend
tail -f logs/backend.log

# Frontend
tail -f logs/frontend.log

# Last 50 errors
grep -i error logs/backend.log | tail -50
```

---

## Making the First Admin

After first startup, promote the first registered user to admin:

```bash
psql "postgresql://barkmind_user:PASSWORD@127.0.0.1:5432/barkmind" \
  -c "UPDATE users SET role='admin' WHERE username='yourusername';"
```

Then create an expert profile at `http://127.0.0.1:3008/expert`.

---

## Quick Health Check

```bash
curl http://127.0.0.1:8108/health
curl http://127.0.0.1:8108/governance/status
curl http://127.0.0.1:8108/.well-known/aegis-meta
```
