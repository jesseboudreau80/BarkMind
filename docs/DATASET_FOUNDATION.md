# BarkMind — Dataset Foundation

**Date:** 2026-05-17  
**Status:** Infrastructure complete, data collection begins

---

## What BarkMind Is Building

BarkMind is not just a review platform. It is building the world's most structured
canine behavioral intelligence dataset. Every case, annotation, taxonomy reference,
confidence level, and expert resolution is a data point.

The platform is designed from day one to produce training-quality behavioral labels.

---

## Dataset Structure

Each case contributes the following labeled data:

### Case-Level Labels
```
Case metadata:
  - setting: daycare | shelter | home | grooming | vet | other
  - subject_age_estimate: puppy | adult | senior
  - subject_breed_note: free text (not normalized yet)
  - trigger_context: what preceded the behavior
  - status: open | under_review | resolved | archived

Expert resolution (ground truth):
  - verdict: safe | concern | escalation_risk | requires_intervention
  - confidence_level: high | medium | low
  - summary: expert narrative
  - recommendations: action items
```

### Annotation-Level Labels
```
Per annotation:
  - annotation_type: observation | interpretation | concern | recommendation
  - body: free text behavioral description
  - confidence_level: high | medium | low (human confidence)
  - is_expert: boolean
  - timestamp_range: [start, end] seconds (for video)
  - taxonomy_refs: list of {slug, category, severity_hint, signal_type}
```

### Timeline-Level Labels
```
Per timeline marker:
  - timestamp_seconds: exact video position
  - marker_type: trigger | escalation | de_escalation | handler_intervention | ...
  - label: annotator-written event description
  - is_expert: boolean
```

### Behavioral Tag Labels
```
Per case-level tag:
  - tag_slug: piloerection | freeze | whale_eye | ...
  - confidence: observed | probable | possible
  - timestamp_note: optional video reference
```

---

## Data Quality Indicators

Every record carries quality signals for future filtering:

| Signal | Source | Meaning |
|---|---|---|
| `is_expert` | User role at write time | Annotation from certified practitioner |
| `confidence_level` | Human-assigned | Annotator's certainty |
| `expert_resolution.verdict` | Role-gated | Ground truth label |
| `annotation.revision_count` | Revision audit | Annotation was reviewed and refined |
| `taxonomy_refs` | Controlled vocabulary | Structured behavioral labels |
| `timeline_markers` | Timestamp-pinned | Temporal behavioral events |

---

## Inter-Rater Reliability Foundation

The data model supports IRR calculation without schema changes:

Multiple users can annotate the same case with the same taxonomy terms.
Overlap analysis: "For case X, what % of annotators used `posture_freeze`?"

Future query pattern:
```sql
SELECT taxonomy_term_id, count(distinct author_id) as annotator_count
FROM annotation_taxonomy_refs atr
JOIN annotations a ON a.id = atr.annotation_id
WHERE a.case_id = $case_id
GROUP BY taxonomy_term_id
HAVING count(distinct author_id) > 1;
```

This enables Cohen's kappa and similar agreement metrics.

---

## Training Dataset Export Shape (Future)

When export is activated, each case produces a JSONL record:

```jsonl
{
  "case_id": "uuid",
  "metadata": {
    "setting": "daycare",
    "subject_age": "adult",
    "trigger": "New reactive terrier approached from front"
  },
  "media": [
    {
      "type": "video",
      "duration_seconds": 12.4,
      "width": 1920,
      "height": 1080
    }
  ],
  "ground_truth": {
    "verdict": "concern",
    "confidence": "high",
    "expert_username": "trainer_jane"
  },
  "annotations": [
    {
      "type": "observation",
      "confidence": "high",
      "is_expert": true,
      "timestamp_range": [3.5, 7.2],
      "taxonomy_terms": [
        {"slug": "posture_piloerection", "severity": 2, "signal": "arousal"},
        {"slug": "posture_stiff", "severity": 3, "signal": "threat"},
        {"slug": "eye_hard_stare", "severity": 3, "signal": "threat"}
      ]
    }
  ],
  "timeline": [
    {"timestamp": 1.0, "type": "trigger", "label": "Dogs introduced"},
    {"timestamp": 3.5, "type": "escalation", "label": "Piloerection onset"},
    {"timestamp": 7.5, "type": "handler_intervention", "label": "Handler body block"}
  ],
  "tags": [
    {"slug": "piloerection", "confidence": "observed"},
    {"slug": "freeze", "confidence": "observed"}
  ]
}
```

---

## Dataset Governance

Per BARKMIND_CONTEXT.md:
- Users retain attribution for their annotations
- Dataset exports require admin approval
- Media included only with submitter consent flag (consent_to_export column — future)
- Expert revisions are always included (they represent the final expert judgment)

---

## AI Training Targets (Future Phases)

| Phase | Training Signal | Target |
|---|---|---|
| Phase 4 (current) | Human annotations + taxonomy | Behavioral vocabulary classification |
| Phase 5 | Timeline markers + video frames | Temporal behavior detection |
| Phase 6 | Expert verdicts as ground truth | Escalation risk scoring |
| Phase 7 | Consensus annotations | High-confidence behavioral labels |

---

## Why This Matters

The BarkMind dataset will be unique because:

1. **Expert-labeled** — not crowdsourced noise but practitioner-annotated
2. **Multi-signal** — text + video + taxonomy + timeline + confidence
3. **Temporal** — timeline markers enable behavioral trajectory modeling
4. **Hierarchical labels** — taxonomy enables both fine-grained and coarse-grained classification
5. **Ground truth** — expert resolutions provide class labels for supervised learning

No equivalent public dataset exists for fine-grained canine behavioral annotation.
