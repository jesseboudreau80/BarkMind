# BarkMind — Governance Model

**Date:** 2026-05-17

---

## Governing Principle

> "Every meaningful action on BarkMind leaves a traceable record."

Governance is not AI oversight. It is human accountability infrastructure.

---

## Audit Event System

Every governance action emits an `AuditEvent`:

```python
await emit_audit_event(
    db,
    event_type="case_locked",
    actor_id=user.id,
    target_type="case",
    target_id=case_id,
    metadata={"lock_state": "full", "reason": "..."}
)
```

Properties:
- **Write-once** — no update or delete
- **Atomic** — created in same transaction as the action
- **Structured** — `event_type`, `actor`, `target_type`, `target_id`, `metadata` JSONB
- **Queryable** — filter by event_type, target, actor, time range

---

## Event Catalog

| Event | Who | When |
|---|---|---|
| `expert_profile_created` | expert | Expert submits profile |
| `expert_verified` | admin | Admin verifies credentials |
| `case_status_changed` | expert/admin | Status transition |
| `expert_assigned` | expert/admin | Case assigned to expert |
| `assignment_claimed` | expert | Expert claims case |
| `case_escalated` | expert/admin | Escalation triggered |
| `consensus_initiated` | expert/admin | Multi-expert review started |
| `consensus_opinion_added` | expert | Expert submits opinion |
| `consensus_reached` | expert | Majority established |
| `resolution_submitted` | expert | Resolution created |
| `resolution_updated` | expert | Resolution edited |
| `case_locked` | expert/admin | Evidence lock applied |
| `case_unlocked` | admin | Evidence lock removed |

---

## Access Levels

| Query | Who Can Access |
|---|---|
| `GET /audit` (full log) | admin only |
| `GET /audit/cases/{id}` (case trail) | expert, admin |
| `GET /audit/governance/summary` | admin only |
| `GET /audit/reputation/{username}` | own user, admin |

---

## Evidence Integrity Model

Evidence locking creates a permanent, immutable record of case state.

**What's in a lock snapshot:**
```json
{
  "case_id": "...",
  "title": "...",
  "status_at_lock": "resolved",
  "submitter": "username",
  "setting": "daycare",
  "annotation_count": 7,
  "tag_count": 4,
  "media_count": 2,
  "resolution": {
    "verdict": "concern",
    "confidence_level": "high",
    "expert": "expert_username",
    "submitted_at": "..."
  }
}
```

This snapshot is stored in `evidence_locks.snapshot` JSONB.
It is the authoritative record of what was reviewed when.

---

## Governance Dashboard (Admin)

`GET /audit/governance/summary` returns:
- Case status distribution (counts by status)
- Total cases, total annotations
- Expert count
- Pending assignments count
- Last 10 audit events

This provides operational visibility without requiring a BI tool.

---

## Future Governance Expansions

| Feature | Prerequisite |
|---|---|
| Compliance export (JSONL) | Evidence locks complete |
| Expert review escalation SLA | Assignment timestamps in place |
| Automated stale case detection | audit_events + created_at |
| Anonymous reporting | audit_events actor_id nullable |
| Cross-case pattern alerts | audit_events + taxonomy_refs join |
| Multi-org governance | user.organization field (not yet normalized) |

All of these build on the current audit event table — no schema changes required.
