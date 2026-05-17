# BarkMind — Consensus System

**Date:** 2026-05-17

---

## What Consensus Is

A consensus review is initiated when:
1. A case is complex or ambiguous
2. A primary expert wants peer validation
3. An admin requires multiple expert opinions
4. A case is disputed or escalated

Consensus is a structured opinion aggregation process. It is NOT:
- Automated AI voting
- Algorithmic ground truth computation
- A replacement for expert judgment

---

## Consensus Lifecycle

```
Admin/Expert → POST /cases/{id}/consensus
  → ConsensusRecord created (status=open)
  → Case status → consensus_pending
  → verdict_tally initialized: {safe:0, concern:0, escalation_risk:0, requires_intervention:0}

Expert 1 → POST /cases/{id}/consensus/opinion
  → ExpertOpinion created (verdict=concern)
  → tally updated: {concern: 1, ...}
  → _derive_consensus() checks majority
  → If reached: ConsensusRecord.status=reached, consensus_verdict set

Expert 2 → POST /cases/{id}/consensus/opinion
  → Same flow — adds to tally
  → consensus_aligned reputation awarded if matches lead
  → consensus_dissented reputation charged if diverges
```

---

## Majority Algorithm

Consensus is derived by vote counting only — no weighting, no AI.

```python
def _derive_consensus(tally: dict) -> tuple[verdict, confidence]:
    total = sum(tally.values())
    if total == 0:
        return None, None

    top_verdict = max(tally, key=lambda k: tally[k])
    pct = tally[top_verdict] / total

    if pct >= 0.75:  return top_verdict, "high"
    if pct >= 0.60:  return top_verdict, "medium"
    if pct >= 0.50:  return top_verdict, "low"

    return None, None  # disputed
```

| Agreement | Confidence | Status |
|---|---|---|
| ≥ 75% | high | reached |
| 60–74% | medium | reached |
| 50–59% | low | reached |
| < 50% | — | open (disputed) |

---

## Consensus vs. Individual Resolution

| Feature | Individual Resolution | Consensus |
|---|---|---|
| Authors | One expert | Multiple experts |
| Record | `expert_resolutions` | `consensus_records` + `expert_opinions` |
| Visibility | Full — verdict, summary, recommendations | Per-opinion (author, verdict, summary) |
| Override | Admin PATCH | Admin close/escalate |
| Lock trigger | Can trigger lock | Can trigger lock |

A case can have BOTH an individual resolution AND a consensus record.
The individual resolution is the formal record; consensus is additional evidence.

---

## Opinion Data Structure

Each `ExpertOpinion`:
- `verdict`: one of `{safe, concern, escalation_risk, requires_intervention}`
- `confidence_level`: high/medium/low (expert's confidence in their own opinion)
- `summary`: expert's reasoning (optional, encouraged)

Opinions are public (visible to admin, other experts).

---

## Consensus Statuses

| Status | Meaning | Transition |
|---|---|---|
| `open` | Accepting opinions | → reached, disputed, escalated |
| `reached` | Majority established | (terminal) |
| `disputed` | No majority — manual resolution needed | → escalated |
| `escalated` | Sent to senior review | (terminal — admin action required) |

There is no automatic dispute resolution. A disputed consensus requires human admin action
(new assignment, new consensus, or override resolution).

---

## Reputation Alignment

When consensus is reached, the system checks each participating expert:
- If their submitted verdict matches the consensus_verdict → `consensus_aligned` (+2)
- If their submitted verdict differs from the leading verdict at submission time → `consensus_dissented` (-1)

This incentivizes careful consideration, not consensus-chasing.

---

## Future: Weighted Consensus

When expert reputation is trusted for weighting:

```
weighted_tally[verdict] = sum(
    expert.reputation_score * opinion.confidence_weight
    for expert, opinion in opinions
    if opinion.verdict == verdict
)
```

Where `confidence_weight = {high: 1.0, medium: 0.75, low: 0.5}`.

This is NOT yet implemented. The current flat counting approach is the baseline.
Weighting requires validation of the reputation signal first.
