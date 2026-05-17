# BarkMind — Expert Reputation Model

**Date:** 2026-05-17

---

## Philosophy

Reputation in BarkMind is a **signal accumulator**, not an algorithm.

It answers: "How much has this expert contributed to behavioral intelligence quality?"

It does NOT answer: "How smart is this expert?" or "How correct are their conclusions?"

---

## Reputation Events

Each event is recorded in `reputation_events` with a `delta` (positive or negative).

| Event | Delta | Trigger |
|---|---|---|
| `expert_verified` | +10 | Admin confirms credentials |
| `resolution_submitted` | +5 | Expert submits a resolution |
| `resolution_accepted` | +3 | Case closed without dispute |
| `consensus_aligned` | +2 | Expert verdict matched final consensus |
| `assignment_claimed` | +1 | Expert claims a case for review |
| `annotation_on_resolved_case` | +1 | Expert annotated a resolved case |
| `consensus_dissented` | -1 | Opinion diverged from emerging consensus |
| `secondary_review_requested` | -1 | Someone requested second opinion on review |

---

## Reputation Score Mechanics

`users.reputation_score` is a running integer sum:
- Starts at 0
- Cannot go below 0 (floor enforced at update time)
- Updated atomically with the trigger action (same transaction)
- Visible on all public expert profiles

---

## What Reputation Does

| Reputation Level | Unlocks |
|---|---|
| 0–9 | Basic expert features |
| 10+ | Verified expert badge eligible |
| 50+ | (Future) Consensus voting priority |
| 100+ | (Future) Consensus initiator rights |

Currently, reputation is display-only. Thresholds are reserved for future phase.

---

## What Reputation Does NOT Do

- Does NOT algorithmically weight annotations
- Does NOT determine case verdicts
- Does NOT auto-promote users to higher roles
- Does NOT penalize honest disagreement (only consensus dissent, not annotations)
- Is NOT calculated by AI

---

## Reputation History

Every reputation change is auditable:

```
GET /audit/reputation/{username}
→ {
    current_score: 13,
    events: [
      {event_type: "expert_verified", delta: +10, ...},
      {event_type: "assignment_claimed", delta: +1, ...},
      {event_type: "consensus_aligned", delta: +2, ...}
    ]
  }
```

---

## Expert Profile Counters

`expert_profiles` stores denormalized counters:
- `review_count` — resolutions submitted, incremented on resolution_submitted
- `annotation_count` — updated periodically (or on annotation create for experts)
- `consensus_agreement_count` — incremented on consensus_aligned event

These counters are for display performance (avoid COUNT queries on every profile load).
They may drift slightly from true counts under high concurrency.

---

## Future: Inter-Rater Reliability

When enough consensus records exist (est. 500+), BarkMind will calculate:

**Cohen's Kappa** between pairs of expert annotators:
```
κ = (Po - Pe) / (1 - Pe)
where:
  Po = observed agreement (fraction of same verdicts)
  Pe = expected agreement by chance
```

This will produce an `agreement_rate` score per expert pair, stored in a future
`expert_agreement_matrix` table. This is the foundation for weighted consensus.

The current `verdict_tally` on `ConsensusRecord` already captures the raw data
needed for this calculation.
