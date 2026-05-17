# BarkMind — Export System

**Date:** 2026-05-17

---

## Export Endpoint

```
POST /exports/{export_type}?format={fmt}
Authorization: Bearer <admin_token>
```

Returns: file download (Content-Disposition: attachment)

Headers in response:
- `X-Export-Count`: number of records
- `X-Export-Type`: export type
- `Content-Disposition`: filename with timestamp

---

## Export Types

### `cases`
Case metadata + expert resolution. Fields:
- id, title, status, setting, subject info
- submitter username
- view_count, created_at, updated_at
- resolution: {verdict, confidence, expert, summary, submitted_at}

### `annotations`
Full annotation records. Fields:
- id, case_id, author, is_expert
- annotation_type, body, confidence_level
- timestamp_start, timestamp_end
- taxonomy_terms: [{slug, label, category}]
- created_at

### `audit`
Complete governance event log. Fields:
- id, event_type, actor, target_type, target_id
- metadata JSONB
- created_at

### `experts`
Expert profile statistics. Fields:
- username, display_title, organization
- verification_status, years_experience
- specializations, certifications
- review_count, annotation_count, reputation_score
- created_at

### `consensus`
Consensus records and opinions. Fields:
- id, case_id, status, initiated_by
- verdict_tally, consensus_verdict, consensus_confidence
- opinion_count
- opinions: [{expert, verdict, confidence, summary}]
- created_at

---

## Formats

### JSON
```json
{
  "export_type": "cases",
  "records": [...],
  "count": 42
}
```

### NDJSON (newline-delimited JSON)
```
{"id":"...","title":"...","status":"locked",...}
{"id":"...","title":"...","status":"resolved",...}
```
One record per line. Streaming-friendly for ML pipelines.

### CSV
Comma-separated values with header row.
Nested objects (resolution, taxonomy_terms) are JSON-encoded strings.
Use NDJSON for ML workflows — CSV is for spreadsheet analysis.

---

## Export Audit Trail

Every export creates an `ExportJob` record:

```
id: UUID
requested_by → users.id
export_type: 'cases'
format: 'ndjson'
status: 'ready'
record_count: 42
parameters: {"export_type": "cases", "format": "ndjson"}
completed_at: 2026-05-17T...
created_at: 2026-05-17T...
```

View export history:
```
GET /exports/history
Authorization: Bearer <admin_token>
```

---

## Security

- Admin role required for all exports
- Every export emits `export_requested` audit event
- Export job records are permanent (never deleted)
- File is returned directly in response (not stored on disk)

Future: large exports → async job + signed download URL
