# BarkMind — Frontend Route Plan

**Stack:** Next.js App Router, TypeScript, Tailwind CSS  
**Base URL:** `https://barkmind.jesseboudreau.com`  
**Internal:** `http://127.0.0.1:3007`  
**Date:** 2026-05-17

---

## Design Philosophy

- App Router (not Pages Router)
- Server Components where possible, Client Components only where necessary
- No excessive loading states — fast, direct
- Scientific and operational aesthetic — not social media
- Mobile-aware but desktop-first (power users are professionals)
- Tailwind for styling — no CSS-in-JS

---

## Build Configuration

```json
"scripts": {
  "build": "next build --webpack",
  "dev": "next dev -p 3007",
  "start": "next start -p 3007"
}
```

`--webpack` required — Turbopack causes ENOENT race conditions on VM builds.

---

## Environment Variables

```
NEXT_PUBLIC_API_URL=https://barkmind-api.jesseboudreau.com
```

Never use `localhost` or `127.0.0.1` in `NEXT_PUBLIC_*` vars.

---

## Route Map

### Public Routes

| Route | Page | Description |
|---|---|---|
| `/` | Landing / Feed | Case feed with filters, community pulse |
| `/cases` | Case Browse | Full case list with search + filter |
| `/cases/[id]` | Case Detail | Full case view: media, tags, annotations, resolution |
| `/cases/[id]/annotate` | Case Annotate | Focused annotation interface |
| `/tags` | Tag Browser | Behavioral vocabulary, sorted by category |
| `/tags/[slug]` | Tag Detail | Cases tagged with this behavior |
| `/users/[username]` | Public Profile | User profile, case history, reputation |

### Auth Routes

| Route | Page | Description |
|---|---|---|
| `/auth/login` | Login | Email + password, JWT response |
| `/auth/register` | Register | Create account |
| `/auth/logout` | Logout | Client-side token clear + redirect |

### Authenticated Routes

| Route | Page | Auth | Description |
|---|---|---|---|
| `/submit` | Submit Case | user+ | Multi-step case submission form |
| `/me` | My Profile | user+ | Own profile, edit display name/bio |
| `/me/cases` | My Cases | user+ | Cases submitted by current user |

### Expert Routes (Role-Gated)

| Route | Page | Role | Description |
|---|---|---|---|
| `/expert` | Expert Queue | expert, admin | Open cases needing resolution |
| `/expert/[id]` | Expert Review | expert, admin | Full review interface with resolution form |

### Admin Routes (Role-Gated)

| Route | Page | Role | Description |
|---|---|---|---|
| `/admin` | Admin Overview | admin | User management, case moderation |
| `/admin/users` | User List | admin | All users, role assignment |
| `/admin/tags` | Tag Management | admin | Create/edit behavioral tags |

---

## Layouts

### `app/layout.tsx` — Root Layout

- Global nav header (logo, links, auth state)
- Footer
- Toast/notification provider

### `app/(main)/layout.tsx` — Main Content Layout

- Sidebar on desktop (optional)
- Content area

### `app/(auth)/layout.tsx` — Auth Layout

- Centered card layout, no sidebar
- Used for `/auth/*`

### `app/(expert)/layout.tsx` — Expert Layout

- Expert-specific sidebar
- Role gate wrapper — redirect to `/` if not expert/admin

---

## Key Components

### Case Feed (`/` and `/cases`)

- Filterable by status, tag, setting
- Each card shows: title, status badge, top tags, media thumbnail, annotation count
- Sort: newest, most active, expert-resolved

### Case Detail (`/cases/[id]`)

Layout sections (top to bottom):
1. **Header** — title, status, submitter, timestamp
2. **Media Gallery** — images/video player, thumbnail strip
3. **Expert Resolution** (if exists) — verdict badge, summary, recommendations
4. **AI Summary** (if exists) — boxed, labeled "AI-Assisted"
5. **Behavioral Tags** — grouped by category, confidence badges
6. **Annotations** — threaded, sorted by expert-first, type-labeled
7. **Community Comments** — threaded, collapsible

### Case Submission (`/submit`)

Multi-step form:
1. **Step 1** — Context: title, setting, subject info, trigger description
2. **Step 2** — Media: image/video upload with progress
3. **Step 3** — Tags: behavioral vocabulary picker (grouped, searchable)
4. **Step 4** — Description: freeform behavioral description
5. **Review + Submit**

### Expert Queue (`/expert`)

- List of open/under_review cases sorted by age
- Quick filters: unresolved, unannotated, expert-flagged
- Resolution form inline or full page

---

## Navigation Structure

**Primary nav:**
- BarkMind (logo) → `/`
- Cases → `/cases`
- Tags → `/tags`
- Submit → `/submit` (auth required, shown always)
- Expert → `/expert` (shown only if role=expert|admin)

**User menu (avatar dropdown):**
- My Profile → `/me`
- My Cases → `/me/cases`
- Admin → `/admin` (if admin)
- Log out

---

## State Management

- Server Components for data fetching where possible
- `SWR` or `fetch` with cache for client-side data
- JWT tokens stored in `httpOnly` cookies set by API response
- No global client-side state store for MVP — keep it simple
- Auth context via React Context (minimal: user object + role)

---

## Error Handling

- `not-found.tsx` per route segment for 404s
- `error.tsx` per route segment for runtime errors
- Auth errors redirect to `/auth/login` with `?return=<path>`
- Expert/admin permission failures show a clear "Access Denied" message (not redirect)

---

## Future Routes (Not in MVP)

| Route | Purpose |
|---|---|
| `/cases/[id]/frames` | Frame-level annotation interface |
| `/datasets` | Training dataset browser and export |
| `/leaderboard` | Reputation rankings |
| `/research` | Published behavioral research integrations |
| `/api-docs` | Embedded OpenAPI docs |
