# BarkMind — Frontend Architecture

**Framework:** Next.js 16 App Router  
**Date:** 2026-05-17

---

## Stack Decisions

### Why Next.js App Router
- Server Components for static public pages (better performance)
- Client Components only where interactivity is needed
- Route groups enable different layouts without URL nesting

### Why TypeScript
- All backend types mirrored in `src/lib/types.ts`
- API client is fully typed — no any-casting in components
- Compile-time safety catches API contract violations

### Why SWR
- Lightweight (no Redux, no React Query overhead)
- Built-in deduplicate, cache, and revalidation
- Simple `useSWR(key, fetcher)` pattern fits the MVP data model

### Why No Global State Store
- Auth state is the only global state (React Context)
- SWR cache handles server state
- No complex client state needed for MVP

### Why Dark-First Design
- Target audience: professional trainers, daycare staff, vets
- Operational platform aesthetic (GitHub × research tool)
- System preference fallback via CSS media query
- Manual toggle deferred to post-MVP

---

## Directory Layout

```
src/
├── app/                        Next.js App Router pages
│   ├── layout.tsx              Root layout: html, body, AuthProvider
│   ├── page.tsx                / → redirect to /cases
│   ├── not-found.tsx           Global 404
│   ├── (auth)/                 Route group: centered card layout
│   │   ├── layout.tsx          Auth-specific layout (no Navbar)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (main)/                 Route group: Navbar layout
│       ├── layout.tsx          Main layout with Navbar + footer
│       ├── cases/
│       │   ├── page.tsx        Case list/browse
│       │   └── [id]/page.tsx   Case detail
│       ├── tags/page.tsx
│       ├── about/page.tsx
│       ├── dashboard/page.tsx
│       ├── upload/page.tsx
│       ├── profile/[username]/page.tsx
│       ├── expert/page.tsx
│       └── moderation/page.tsx
├── components/
│   ├── ui/                     Primitive UI components
│   │   ├── Badge.tsx           Colored tag/label
│   │   ├── Button.tsx          Primary/secondary/ghost/danger variants
│   │   ├── Card.tsx            Surface container
│   │   ├── Input.tsx           Input, Textarea, Select
│   │   └── Spinner.tsx         Loading indicators
│   ├── layout/
│   │   └── Navbar.tsx          Sticky top nav with auth state
│   ├── cases/                  Case-domain components
│   │   ├── CaseCard.tsx        Card for case list items
│   │   ├── StatusBadge.tsx     Open/Under Review/Resolved/Archived
│   │   ├── VerdictBadge.tsx    Safe/Concern/Escalation/Intervention
│   │   ├── TagBadge.tsx        TagBadge + CaseTagBadge (with confidence)
│   │   ├── MediaGallery.tsx    Image/video viewer with thumbnail strip
│   │   ├── AnnotationList.tsx  Structured annotation display
│   │   ├── CommentThread.tsx   Threaded comments with reply form
│   │   └── ExpertResolutionPanel.tsx  Verdict + summary + recommendations
│   └── forms/
│       └── AnnotationForm.tsx  Add annotation form (collapsible)
├── contexts/
│   └── AuthContext.tsx         JWT auth state (user, token, login, logout)
└── lib/
    ├── types.ts                TypeScript interfaces mirroring API responses
    ├── api.ts                  Typed API client (fetch wrapper + domain functions)
    └── utils.ts                Date formatting, cn(), severity helpers
```

---

## API Integration Architecture

### Proxy Pattern

All client-side API calls use the relative path `/api-backend/*`:

```
Browser → /api-backend/cases → Next.js Server → BACKEND_INTERNAL_URL/cases
```

This keeps internal addresses out of client bundles while allowing flexible deployment.

**Configuration:**
```
BACKEND_INTERNAL_URL=http://127.0.0.1:8107  (server-side, not NEXT_PUBLIC)
NEXT_PUBLIC_API_URL=https://barkmind-api.jesseboudreau.com  (for display links only)
```

**Local dev override** (in `.env.local`, gitignored):
```
BACKEND_INTERNAL_URL=http://127.0.0.1:8108  (while port 8107 is occupied)
```

### API Client (`lib/api.ts`)

Domain-namespaced typed functions:
```ts
auth.login(email, password) → LoginResponse
auth.me() → User
cases.list(params) → CaseListResponse
cases.get(id) → CaseDetail
tags.list() → TagsGrouped
tags.applyToCase(caseId, body) → { id, applied }
media.upload(caseId, file, onProgress) → MediaResponse
resolutions.create(caseId, body) → { id, verdict }
```

Token is read from `localStorage` for each request automatically.

---

## Auth Architecture

```
Login → POST /api-backend/auth/login → { access_token, refresh_token }
      → localStorage.setItem('barkmind_token', access_token)
      → AuthContext.setUser(me)

Every API request → getStoredToken() → Authorization: Bearer <token>

Logout → localStorage.clear() → AuthContext.setUser(null) → redirect /
```

Protected pages check `useAuth().user` on mount. If null after loading, redirect to
`/login?return=<current-path>`.

Role checks:
- Expert queue: requires `role === 'expert' || role === 'admin'`
- Moderation: requires `role === 'admin'`
- Resolution submission: enforced at API level

---

## Design System

### Color Tokens (via CSS variables in globals.css)

```css
--bg-base:       #09090b   /* zinc-950 — page background */
--bg-surface:    #18181b   /* zinc-900 — cards */
--bg-elevated:   #27272a   /* zinc-800 — inputs, hover states */
--border:        #3f3f46   /* zinc-700 — default borders */
--text-primary:  #f4f4f5   /* zinc-100 */
--text-secondary:#a1a1aa   /* zinc-400 */
--text-muted:    #71717a   /* zinc-600 */
--accent:        #f59e0b   /* amber-400 — BarkMind brand */
```

### Status → Color Mapping

| Status | Color |
|---|---|
| open | blue |
| under_review | amber |
| resolved | emerald |
| archived | zinc |

### Verdict → Color Mapping

| Verdict | Color |
|---|---|
| safe | emerald |
| concern | amber |
| escalation_risk | orange |
| requires_intervention | red |

### Tag Severity → Color

| Severity | Color |
|---|---|
| 0 (info) | zinc-400 |
| 1 (mild) | blue-400 |
| 2 (moderate) | amber-400 |
| 3 (elevated) | orange-400 |
| 4 (severe) | red-400 |

---

## Tailwind 4 Notes

Tailwind 4 is configured via CSS, not `tailwind.config.js`:

```css
/* globals.css */
@import "tailwindcss";

@theme inline {
  --color-background: var(--bg-base);
  --color-foreground: var(--text-primary);
}
```

No JavaScript config file needed. All customization via CSS variables and `@theme`.

Dark mode: designed as always-dark (system preference via CSS media query as fallback).
Manual toggle deferred to future phase.

---

## Key Conventions

1. `"use client"` only on components that need browser APIs or React state/effects
2. SWR keys are namespaced: `"cases"`, `"tags"`, `` `case:${id}` ``, `` `profile:${username}` ``
3. Error states show human-readable messages, not raw HTTP codes
4. Loading states use `<PageSpinner>` for full-page loads, inline spinners for actions
5. Auth redirects preserve the `?return=<path>` query param
6. All forms use controlled inputs (not uncontrolled refs)
7. `cn()` utility from `clsx` for conditional classNames
