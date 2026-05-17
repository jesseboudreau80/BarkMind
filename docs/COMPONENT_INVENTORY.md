# BarkMind — Component Inventory

**Date:** 2026-05-17  
**Phase:** 2 Complete

---

## UI Primitives (`src/components/ui/`)

### Badge
**File:** `ui/Badge.tsx`  
**Purpose:** Inline label with color variants  
**Variants:** `default`, `amber`, `blue`, `green`, `red`, `orange`, `zinc`  
**Used by:** StatusBadge, VerdictBadge, AnnotationList

### Button
**File:** `ui/Button.tsx`  
**Purpose:** Interactive action button  
**Variants:** `primary` (amber), `secondary` (zinc), `ghost` (text only), `danger` (red)  
**Sizes:** `sm`, `md`, `lg`  
**Props:** `isLoading` shows spinner + disables; `variant`, `size`

### Card
**File:** `ui/Card.tsx`  
**Purpose:** Surface container for grouped content  
**Props:** `hover` (adds hover effect), `onClick` (makes it clickable)  
**Sub-component:** `CardSection` for bordered internal sections

### Input, Textarea, Select
**File:** `ui/Input.tsx`  
**Purpose:** Form input primitives  
**All support:** `label`, `error` props  
**Style:** Dark zinc background, amber focus ring

### Spinner, PageSpinner
**File:** `ui/Spinner.tsx`  
**Purpose:** Loading indicators  
**Sizes:** `sm`, `md`, `lg`  
**`PageSpinner`:** Centered full-height spinner for page-level loading

---

## Layout Components (`src/components/layout/`)

### Navbar
**File:** `layout/Navbar.tsx`  
**Purpose:** Sticky top navigation  
**Features:**
- BarkMind logo → `/`
- Primary nav links (Cases, Tags, About)
- Expert link (shown only if role = expert/admin)
- Submit Case button (authenticated)
- User menu dropdown (profile, dashboard, admin, logout)
- Unauthenticated: Sign in + Register buttons

---

## Case Components (`src/components/cases/`)

### CaseCard
**File:** `cases/CaseCard.tsx`  
**Purpose:** Card display of a case list item  
**Shows:** Status badge, setting, title, submitter, view count, tags (up to 4)  
**Click:** navigates to `/cases/{id}`  
**Submitter click:** navigates to `/profile/{username}`

### StatusBadge
**File:** `cases/StatusBadge.tsx`  
**Purpose:** Colored badge for case status  
**States:** open (blue), under_review (amber), resolved (green), archived (zinc)

### VerdictBadge
**File:** `cases/VerdictBadge.tsx`  
**Purpose:** Colored badge for expert resolution verdict  
**States:** safe (green), concern (amber), escalation_risk (orange), requires_intervention (red)

### TagBadge / CaseTagBadge
**File:** `cases/TagBadge.tsx`  
**`TagBadge`:** Displays a raw `Tag` object with severity dot  
**`CaseTagBadge`:** Displays a `CaseTag` with confidence opacity and tooltip

### MediaGallery
**File:** `cases/MediaGallery.tsx`  
**Purpose:** Image/video viewer for case media  
**Features:**
- Main viewer (image: `<img>`, video: `<video controls>`)
- Thumbnail strip for multiple files
- Active thumbnail highlighted with amber border
- File info row (name, MIME, size)
- Empty state with placeholder icon

### AnnotationList
**File:** `cases/AnnotationList.tsx`  
**Purpose:** Displays structured behavioral annotations  
**Features:**
- Type badge (Observation/Interpretation/Concern/Recommendation)
- Expert badge (amber, with Shield icon) for expert annotations
- Author + timestamp
- Timestamp range display (video timestamps)
- Empty state

### CommentThread
**File:** `cases/CommentThread.tsx`  
**Purpose:** Threaded community comments with reply form  
**Features:**
- Top-level comments with indented replies
- Reply button per comment (authenticated only)
- New comment form with submit
- Loads fresh comment list from API after each post
- Unauthenticated: shows sign-in link

### ExpertResolutionPanel
**File:** `cases/ExpertResolutionPanel.tsx`  
**Purpose:** Displays formal expert verdict  
**Shows:** Verdict badge, confidence level, expert username, date, summary, recommendations  
**Style:** Bordered panel with Shield icon header

---

## Form Components (`src/components/forms/`)

### AnnotationForm
**File:** `forms/AnnotationForm.tsx`  
**Purpose:** Collapsible form to add structured annotations  
**Fields:** Type (select), body (textarea), timestamp start/end  
**Behavior:** Shows as "+ Add Annotation" button, expands to form, collapses on submit/cancel  
**Callback:** `onAdded()` triggers case data refresh

---

## Auth Context (`src/contexts/AuthContext.tsx`)

**Provides:**
```ts
user: User | null
token: string | null
isLoading: boolean
login(email, password): Promise<void>
register(email, username, password, displayName?): Promise<void>
logout(): void
```

**Token persistence:** `localStorage.barkmind_token` + `localStorage.barkmind_refresh_token`  
**Startup:** Reads token from storage, validates with `/auth/me`, sets user state  
**Hook:** `useAuth()` — throws if used outside `AuthProvider`

---

## Pages Summary

| Page | Client/Server | Auth Required | Role |
|---|---|---|---|
| `/` | Server | No | — |
| `/cases` | Client | No | — |
| `/cases/[id]` | Client | No (optional) | — |
| `/tags` | Client | No | — |
| `/about` | Server | No | — |
| `/login` | Client | No | — |
| `/register` | Client | No | — |
| `/dashboard` | Client | Yes | any |
| `/upload` | Client | Yes | any |
| `/profile/[username]` | Client | No | — |
| `/expert` | Client | Yes | expert, admin |
| `/moderation` | Client | Yes | admin |

---

## Components Not Yet Implemented (Future Phases)

| Component | Phase | Description |
|---|---|---|
| `ResolutionForm` | Phase 5 | Inline expert resolution form |
| `TagManagement` | Phase 5 | Admin tag CRUD |
| `UserManagement` | Phase 5 | Admin user list + role editor |
| `FrameAnnotator` | Post-MVP | Per-frame video annotation |
| `AISummaryTrigger` | Phase 4 | Expert button to trigger AI summary |
| `ThemeToggle` | Post-MVP | Dark/light mode switch |
