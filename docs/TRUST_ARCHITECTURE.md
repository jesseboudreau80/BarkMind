# BarkMind — Trust Architecture

**Date:** 2026-05-17  
**Phase:** 5

---

## Trust Layers

BarkMind's trust system operates in four layers, each building on the previous:

```
Layer 4: Evidence Integrity
  ├── Immutable evidence locks
  ├── Case state snapshots
  └── Annotation freeze

Layer 3: Governance Visibility
  ├── Audit event log (write-once)
  ├── Reputation event history
  └── Assignment traceability

Layer 2: Expert Credentialing
  ├── Professional profiles
  ├── Certification records
  ├── Verification status
  └── Specialization taxonomy

Layer 1: Review Accountability
  ├── Author attribution (all records)
  ├── Role-aware permissions
  ├── Immutable annotation revisions
  └── Timestamp on every action
```

---

## Expert Verification

Expert profiles are not self-certified. The verification lifecycle:

```
User (role=expert) creates ExpertProfile
  → verification_status: "pending"
  → Admin reviews credentials
  → Admin calls PATCH /experts/{id}/verify
  → verification_status: "verified"
  → +10 reputation event
  → audit_event: expert_verified
```

Verified experts are:
- Highlighted with a ✓ badge in the UI
- Listed first in expert discovery
- Their annotations are visually distinguished (`is_expert=true`)
- Their resolutions carry the highest platform credibility

---

## Review Assignment Chain

Assignment lifecycle with full traceability:

```
Admin → POST /cases/{id}/assign → ReviewAssignment (status=pending)
Expert → POST /cases/{id}/claim → status=claimed, claimed_at=NOW
  → audit_event: assignment_claimed
  → reputation: +1
Expert reviews, annotates, submits resolution
  → audit_event: resolution_submitted
  → reputation: +5
Admin/Expert → POST /cases/{id}/lock → EvidenceLock
  → audit_event: case_locked
```

If review needs escalation:
```
Expert → POST /cases/{id}/escalate
  → case.status = escalated
  → audit_event: case_escalated
  → New assignment created with review_type=escalation
```

Transfer chain via `transferred_from` FK on ReviewAssignment preserves the full
review custody chain.

---

## Evidence Integrity

When a case is locked:
1. `EvidenceLock` record is created (write-once)
2. `case.status` → "locked"
3. Snapshot captured: verdict, annotation count, media count, resolution details
4. `audit_event: case_locked` emitted

After locking:
- New annotations: blocked at router level
- Annotation edits: blocked at router level
- Media deletion: blocked at router level
- Resolution updates: blocked unless admin forces

The snapshot is the permanent dataset record — the exact state of the case at the
moment it was reviewed and accepted as evidence.

---

## Audit Event Guarantees

AuditEvent records:
- Are created in the same database transaction as the action they record
- Have no `updated_at` column — they cannot be modified
- Are never soft-deleted
- Include: event_type, actor_id, target_type, target_id, metadata JSONB

If the action fails (transaction rollback), the audit event is also rolled back.
If the action succeeds, the audit event is committed atomically with it.

---

## Reputation System Design

Reputation is a signal, not a score. It reflects:
- Quantity of expert activity (reviews, annotations)
- Quality signals (consensus alignment, accepted resolutions)
- Governance actions (verification)

It does NOT reflect:
- AI assessment of annotation quality
- Automated behavioral scoring
- Peer rating of annotations

Reputation cannot be spent or transferred. It accumulates permanently with small
penalties for governance friction (consensus dissent, secondary review requests).

---

## Role-Permission Matrix

| Action | user | expert | admin |
|---|---|---|---|
| Submit case | ✓ | ✓ | ✓ |
| Annotate case | ✓ | ✓ | ✓ |
| Submit resolution | ✗ | ✓ | ✓ |
| Assign case | ✗ | ✓ | ✓ |
| Claim case | ✗ | ✓ | ✓ |
| Escalate case | ✗ | ✓ | ✓ |
| Initiate consensus | ✗ | ✓ | ✓ |
| Submit consensus opinion | ✗ | ✓ | ✓ |
| Lock evidence | ✗ | ✓ | ✓ |
| Unlock evidence | ✗ | ✗ | ✓ |
| Verify expert profile | ✗ | ✗ | ✓ |
| Read audit log (full) | ✗ | ✗ | ✓ |
| Read case audit trail | ✗ | ✓ | ✓ |
| Change user roles | ✗ | ✗ | ✓ |

---

## Future: Graduated Trust

The current system uses binary role trust (user/expert/admin).
Future phases may add:

- **Trust levels** within the expert role (junior/senior/master)
- **Domain-specific trust** (e.g., "trusted for daycare cases" vs "trusted for shelter")
- **Verification tiers** (community-verified vs credential-verified vs institution-verified)
- **Reputation thresholds** gating features (e.g., consensus vote requires rep ≥ 50)

All of this is addable without schema changes — it builds on `reputation_score`,
`expert_profiles.verification_status`, and `expert_profiles.specializations`.
