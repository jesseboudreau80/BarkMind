# BarkMind — Telemetry Model

**Date:** 2026-05-17

---

## What Telemetry Measures

BarkMind telemetry tracks operational signals — not behavioral conclusions.

| Signal | Measure | Purpose |
|---|---|---|
| Case velocity | Cases created per day/week | Dataset growth rate |
| Annotation velocity | Annotations per day | Community engagement |
| Resolution throughput | Resolutions per week | Expert productivity |
| Consensus frequency | Consensus reviews initiated | Complex case rate |
| Escalation rate | Escalations per resolved case | Quality signal |
| Taxonomy adoption | % annotations with taxonomy refs | Annotation quality |
| Export volume | Exports per week | Data access patterns |
| Stale review count | Assignments > 7 days pending | Workflow health |
| Active users (24h) | Distinct actors in audit log | Platform activity |

---

## Telemetry Endpoints

### `/governance/status`
No auth required. Returns comprehensive platform status including:
- `status`: operational/degraded
- `capabilities[]`: 13 declared capabilities
- `metrics{}`: live counts
- `compliance{}`: governance requirement checklist

Consumed by: Aegis governance platform, uptime monitors

### `/governance/metrics`
No auth required. Returns quantitative metrics:
- Platform totals (cases, users, annotations, media, locked)
- Activity metrics (active users 24h, events 7d, top event types)

Consumed by: Aegis dashboard, operational monitoring

### `/telemetry/events`
Auth: expert/admin or X-Service-Key header.
Paginated event stream with filters and replay capability.

### `/telemetry/summary`
Auth: admin.
Event volume by type for the last 7 days.

### `/telemetry/ops`
Auth: expert/admin.
Live ops overview: stale reviews, pending assignments, open consensus, escalations.

---

## Analytics vs. Telemetry

| Concern | Telemetry | Analytics |
|---|---|---|
| Freshness | Real-time (live DB queries) | Same (computed on demand) |
| Audience | Aegis, ops monitoring | Admin dashboards |
| Auth | None or service key | Admin JWT |
| Aggregation | Minimal (live counts) | Full (distributions, rates) |
| Export | Event stream | Analytics summary |

---

## Metrics Freshness

All telemetry is computed on-demand from PostgreSQL.
There is no caching layer — every request runs fresh queries.

This ensures correctness at the cost of latency.
For high-volume deployments, add Redis caching with 60s TTL on `/governance/metrics`.

---

## No AI in Telemetry

All metrics are:
- Counts of human actions
- Percentages of those counts
- Time-based rates

No predictive scoring. No anomaly detection. No automated alerts.

Operators read these metrics and make judgments.
