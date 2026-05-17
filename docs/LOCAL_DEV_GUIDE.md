# BarkMind — Local Development Guide

**Date:** 2026-05-17  
**Phase:** 1 (Backend Core complete)

---

## Prerequisites

- Python 3.12+
- PostgreSQL 18 (running on `127.0.0.1:5432`)
- `uvicorn` in PATH (`pip install uvicorn` or system package)
- All packages: `pip install -r backend/requirements.txt --break-system-packages`

---

## PORT CONFLICT NOTICE

**Port 8107 is currently occupied by `aegis-lite` (PID 41580).**

Before BarkMind can start normally, resolve this conflict:

```bash
# Check what's on 8107
lsof -i:8107

# If aegis-lite is unused, stop it:
kill $(lsof -ti:8107)

# Verify it's free:
lsof -i:8107 || echo "Port 8107 is free"
```

If aegis-lite is an active service, check the Aegis port registry:
```bash
curl http://127.0.0.1:8102/infrastructure/ports -H "X-User-Email: admin@dpvet.com"
```

---

## First Time Setup

### 1. Copy and configure .env

```bash
cp .env.example .env
# .env is pre-configured for local dev — values are already set
# Change JWT_SECRET before any real deployment
```

### 2. Database setup (already done for this machine)

```bash
sudo -u postgres psql <<SQL
CREATE USER barkmind_user WITH PASSWORD 'barkmind_dev_password';
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
```

### 4. Start backend

```bash
./start.sh
```

Or directly:
```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8107 --reload
```

The `--reload` flag enables hot-reload during development.

Tags are seeded automatically on first startup.

---

## Development Workflow

### Running with hot-reload

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8107 --reload --log-level debug
```

### Checking runtime status

```bash
./status.sh
```

### Viewing logs

```bash
tail -f logs/backend.log
```

---

## Database Operations

### Connect to database

```bash
psql "postgresql://barkmind_user:barkmind_dev_password@127.0.0.1:5432/barkmind"
```

### Useful queries

```sql
-- List all tables
\dt

-- View all users
SELECT id, email, username, role, created_at FROM users;

-- View all cases with submitter
SELECT c.id, c.title, c.status, u.username
FROM cases c JOIN users u ON c.submitter_id = u.id
ORDER BY c.created_at DESC;

-- Count tags per category
SELECT category, count(*) FROM tags GROUP BY category ORDER BY category;

-- Promote user to expert
UPDATE users SET role='expert' WHERE username='myusername';

-- Promote user to admin
UPDATE users SET role='admin' WHERE username='myusername';
```

### Creating a new migration

After changing models:

```bash
cd backend
alembic revision --autogenerate -m "describe_the_change"
alembic upgrade head
```

### Rolling back a migration

```bash
cd backend
alembic downgrade -1
```

### Viewing migration history

```bash
cd backend
alembic history
alembic current
```

---

## Reset for Clean Testing

```bash
# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS barkmind;"
sudo -u postgres psql -c "CREATE DATABASE barkmind OWNER barkmind_user;"
sudo -u postgres psql -d barkmind -c "GRANT ALL ON SCHEMA public TO barkmind_user;"

# Re-run migrations
cd backend && alembic upgrade head

# Tags re-seed automatically on next startup
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `BACKEND_PORT` | `8107` | FastAPI server port — canonical, do not change |
| `FRONTEND_PORT` | `3007` | Next.js port — canonical, do not change |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async PostgreSQL URL |
| `JWT_SECRET` | (set in .env) | Must be a long random string in production |
| `JWT_ACCESS_EXPIRE_MINUTES` | `60` | Access token TTL |
| `JWT_REFRESH_EXPIRE_DAYS` | `30` | Refresh token TTL |
| `MEDIA_ROOT` | `./media` | Local media storage root (relative to backend/) |
| `MEDIA_BACKEND` | `local` | `local` or `s3` |
| `OPENCLAW_BASE_URL` | `http://127.0.0.1:18789` | AI gateway URL |
| `AEGIS_BASE_URL` | `http://127.0.0.1:8102` | Governance registration URL |
| `LOG_LEVEL` | `INFO` | Python logging level |

---

## Media Storage

Uploaded files are stored at:

```
./media/
  cases/
    {case_id}/
      original/
        {media_id}.{ext}    ← uploaded file
      thumbnails/           ← Phase 3: generated thumbnails
```

Media is served at `http://127.0.0.1:8107/media/...`

In development, the media root is `./media` relative to `backend/`. Set `MEDIA_ROOT` to an absolute
path for production.

---

## API Quick Reference

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/health` | GET | — | Liveness check |
| `/auth/register` | POST | — | Create account |
| `/auth/login` | POST | — | Get JWT tokens |
| `/auth/me` | GET | Bearer | Own profile |
| `/cases` | GET | Optional | Browse cases |
| `/cases` | POST | Bearer | Create case |
| `/cases/{id}` | GET | Optional | Case detail |
| `/cases/{id}/tags` | POST | Bearer | Apply tag |
| `/cases/{id}/annotations` | POST | Bearer | Add annotation |
| `/cases/{id}/comments` | POST | Bearer | Add comment |
| `/cases/{id}/media` | POST | Bearer | Upload media |
| `/cases/{id}/resolution` | POST | Expert+ | Submit verdict |
| `/tags` | GET | — | All tags grouped |
| `/users/{username}` | GET | Optional | Public profile |
| `/docs` | GET | — | OpenAPI docs |

Full reference: `docs/API_TESTING_GUIDE.md`

---

## Phase 2 Next Steps

When ready to start Phase 2 (Next.js frontend):

1. Resolve port 8107 conflict
2. Confirm backend starts cleanly via `./start.sh`
3. Initialize Next.js in `frontend/`
4. Set `NEXT_PUBLIC_API_URL=https://barkmind-api.jesseboudreau.com` in frontend env
5. Implement auth flow (login, register, JWT storage in httpOnly cookie)

See `docs/FRONTEND_ROUTE_PLAN.md` for the full Next.js plan.
