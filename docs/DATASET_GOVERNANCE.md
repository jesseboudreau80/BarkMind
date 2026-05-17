# BarkMind — Dataset Governance

**Date:** 2026-05-17

---

## What Is the BarkMind Dataset

BarkMind accumulates a structured behavioral intelligence dataset from:
- Expert-annotated behavior cases
- Taxonomy-referenced annotations
- Expert consensus verdicts
- Timeline behavioral markers
- Evidence-locked case snapshots

Every annotation has: author attribution, expert credentialing, confidence level,
revision history, and taxonomy references. This is dataset-quality metadata.

---

## Dataset Versioning

**Dataset Snapshots** provide versioned metadata captures.

A snapshot records: case count, annotation count, expert count, status distribution,
taxonomy adoption, and full aggregate statistics — at a specific point in time.

Snapshots are NOT the data — they are metadata about the data at a moment.
Use exports to get the actual records.

```
POST /dataset/snapshot
  ?name=production-2026-q1
  &version_tag=v1.0.0
  &description=First production dataset snapshot
```

Response includes comprehensive statistics:
- case_count, annotation_count, expert_count
- status_distribution, setting_distribution
- annotation_type_distribution, taxonomy_category_usage
- consensus_agreement_rate
- top_taxonomy_terms

---

## Annotation Lineage

`GET /dataset/lineage/{case_id}` returns the complete provenance chain:

```json
{
  "annotation_id": "...",
  "annotation_type": "observation",
  "confidence_level": "high",
  "is_expert": true,
  "author": {
    "username": "trainer_jane",
    "role": "expert",
    "verification_status": "verified",
    "display_title": "CPDT-KA"
  },
  "taxonomy_terms": [...],
  "revision_count": 1,
  "revisions": [
    {
      "editor": "trainer_jane",
      "change_reason": "Added anatomical detail",
      "previous_body": "...",
      "revised_at": "..."
    }
  ]
}
```

This is the evidence chain for every data point in the dataset.

---

## Evidence Locking

When a case is locked:
1. No new annotations can be added
2. No existing annotations can be edited
3. No media can be deleted
4. An immutable snapshot is stored in `evidence_locks.snapshot`

The snapshot IS the permanent dataset record. It captures the complete
reviewable state at the moment of expert acceptance.

---

## Export System

Exports are available in three formats:

| Format | Use Case |
|---|---|
| `json` | Default. Human-readable, nested structures |
| `ndjson` | Machine learning pipelines. One record per line |
| `csv` | Spreadsheet analysis. Nested fields are JSON-encoded strings |

Supported export types:

| Type | Content |
|---|---|
| `cases` | Case metadata + expert resolutions |
| `annotations` | Full annotation records with taxonomy refs |
| `audit` | Complete governance event log |
| `experts` | Expert profile statistics |
| `consensus` | Consensus records and opinions |

Every export is logged in `export_jobs` with: requester, timestamp, type, format, record count.
This is the export audit trail for compliance.

---

## Data Access Control

| Action | Role Required |
|---|---|
| Download any export | admin |
| View export history | admin |
| Create dataset snapshot | admin |
| View snapshots | admin |
| View annotation lineage | expert, admin |

---

## Dataset Quality Signals

Available on every annotation:

| Signal | Field | Meaning |
|---|---|---|
| Expert authored | `is_expert` | Author had expert role at annotation time |
| Verified expert | `author.verification_status` | Author credentials were verified by admin |
| Human confidence | `confidence_level` | high/medium/low |
| Taxonomy referenced | `taxonomy_terms[]` | Controlled vocabulary annotation |
| Reviewed and edited | `revision_count > 0` | Annotation was refined |

---

## Future: Training Dataset Release

When the dataset is ready for external release:

1. Create a named snapshot (`POST /dataset/snapshot`)
2. Export cases + annotations as NDJSON (`POST /exports/cases?format=ndjson`)
3. Tag the export job with the snapshot ID
4. Compute dataset statistics from snapshot metadata
5. Generate dataset card (model card format)

The export system, snapshot system, and lineage system are all in place.
Only the dataset card generation and external distribution tooling remain.
