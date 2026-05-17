# BarkMind — Annotation Architecture

**Date:** 2026-05-17  
**Phase:** 4

---

## Design Principles

1. **Human intelligence first.** Annotations are human observations, not AI outputs.
2. **Precision over volume.** Confidence levels and taxonomy refs make each annotation more useful than free-text alone.
3. **Immutable audit trail.** Edits create revisions — the original record is preserved.
4. **Author attribution.** Every annotation is permanently tied to its author.
5. **Extensibility.** JSONB `extra_data` handles edge cases; taxonomy handles structure.

---

## Annotation Types

| Type | Meaning | Who uses it |
|---|---|---|
| `observation` | What the annotator directly saw | Anyone |
| `interpretation` | What the behavior likely means | Experts preferred |
| `concern` | Something that warrants attention | Anyone |
| `recommendation` | Suggested action or intervention | Experts |

Expert annotations are visually distinguished. A user with `role=expert` automatically gets `is_expert=true` on their annotations.

---

## Confidence Levels

Human confidence in the annotation (not AI confidence):

| Level | Meaning |
|---|---|
| `high` | Annotator is certain of what they observed and how to categorize it |
| `medium` | Observed clearly, interpretation has some uncertainty |
| `low` | Possible observation, may need corroboration |

Confidence is stored as a first-class column (not in `extra_data`) for queryability.

---

## Taxonomy Reference System

An annotation can reference 0–N taxonomy terms. Taxonomy terms provide:
- Controlled vocabulary (no free-form label variation)
- Category organization (body_posture, tail_position, etc.)
- Severity hints (0=informational, 4=severe)
- Signal type metadata (threat, appeasement, play, neutral, etc.)

```
Annotation
  ├── body: "Subject showed stiffening and piloerection..."
  ├── confidence_level: "high"
  └── taxonomy_refs:
        ├── posture_piloerection  (body_posture, severity=2, signal=arousal)
        ├── posture_stiff         (body_posture, severity=3, signal=threat)
        └── eye_hard_stare        (eye_contact, severity=3, signal=threat)
```

This structure enables:
- Filtering annotations by behavioral category
- Cross-case behavior frequency analysis
- Future: inter-rater reliability (multiple annotators on same taxonomy terms)
- Future: dataset export with structured behavioral labels

---

## Revision History

Every edit to an annotation creates an `AnnotationRevision` record:

```
annotation_revisions:
  id: UUID
  annotation_id → annotations.id
  revised_by → users.id
  previous_body: TEXT
  previous_annotation_type: TEXT
  previous_confidence_level: TEXT
  previous_extra_data: JSONB
  change_reason: TEXT
  created_at: TIMESTAMPTZ (immutable)
```

Revisions are **write-once** and are never updated. The current annotation reflects the latest state; revisions capture all previous states.

**Why:** Behavioral annotation in clinical contexts must be auditable. An expert changing their assessment after new information should be traceable.

---

## Timeline Markers

Timeline markers are distinct from annotations. They are:
- Pinned to exact timestamps (not ranges)
- Typed (trigger, escalation, etc.)
- Lightweight — no full body text required
- Linked to a specific media file (optional)

Relationship:
```
Case
  └── timeline_markers (ordered by timestamp_seconds)
        ├── media_id → case_media.id (optional)
        ├── marker_type: escalation
        ├── label: "Piloerection onset"
        └── timestamp_seconds: 3.5
```

Use case: Expert watches a video and marks: "trigger at 1s, escalation at 3.5s, handler block at 7.5s". These become the behavioral timeline.

Future: Timeline markers will be the seed points for AI frame extraction (Phase 5).

---

## Annotation ↔ Timeline Relationship

An annotation with `timestamp_start` and `timestamp_end` is linked to a video range.
A timeline marker is linked to a specific point.

They complement each other:
- Annotation: "Freeze posture during 3.5–7.2s" (detailed, ranged)
- Timeline marker: "Freeze onset" @ 3.5s (quick, point-in-time)

---

## Filtering Capabilities

The annotation list endpoint supports:
```
GET /cases/{id}/annotations
  ?annotation_type=observation
  &confidence=high
  &expert_only=true
  &has_taxonomy=true
  &timestamp_min=3.0
  &timestamp_max=8.0
```

All filters can be combined. Results are always ordered expert-first, then chronological.

---

## Future: Consensus Scoring

The data structure supports inter-rater reliability without modification:
- Multiple annotators apply taxonomy refs to the same annotation
- `annotation_taxonomy_refs` has `(annotation_id, taxonomy_term_id)` unique constraint per user
- Future query: "For case X, how often do different annotators agree on posture_stiff?"

This is the foundation for consensus-based ground truth labeling.

---

## Dataset Export Shape (Future)

Each annotation contributes a structured record:
```json
{
  "case_id": "...",
  "annotation_id": "...",
  "author_role": "expert",
  "annotation_type": "observation",
  "confidence": "high",
  "timestamp_range": [3.5, 7.2],
  "body": "...",
  "taxonomy_terms": [
    {"slug": "posture_piloerection", "category": "body_posture", "severity": 2},
    {"slug": "posture_stiff", "category": "body_posture", "severity": 3},
    {"slug": "eye_hard_stare", "category": "eye_contact", "severity": 3}
  ],
  "revision_count": 1,
  "created_at": "..."
}
```
