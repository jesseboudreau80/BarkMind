# BarkMind — Event Architecture

**Date:** 2026-05-17

---

## Design

BarkMind uses an **append-only event log** backed by PostgreSQL.

Every significant platform action emits a typed event.
Events are:
- Never modified after creation
- Committed atomically with the action that produced them
- Queryable with filters (type, actor, target, since)
- Replayable from any timestamp

---

## Event Publisher

`services/event_publisher.py` provides the abstraction:

```python
# Typed event constructors
event = case_resolved(actor_id=user.id, case_id=case_id, verdict="concern")

# Publish (writes to audit_events table)
await publish(db, event)
```

**Future migration path:** Replace `_persist_event()` in `event_publisher.py`
to emit to Kafka, NATS, or SQS. All callers remain unchanged.

---

## Event Catalog

### Case Lifecycle
| Event | Trigger |
|---|---|
| `case_created` | Case submitted |
| `case_status_changed` | Status transition |
| `case_resolved` | Expert resolution submitted |
| `case_locked` | Evidence lock applied |
| `case_unlocked` | Admin removes lock |
| `case_escalated` | Escalation triggered |

### Annotation Events
| Event | Trigger |
|---|---|
| `annotation_created` | New annotation added |
| `annotation_revised` | Annotation edited |

### Expert & Consensus
| Event | Trigger |
|---|---|
| `expert_profile_created` | Expert creates profile |
| `expert_verified` | Admin verifies credentials |
| `expert_assigned` | Case assigned to expert |
| `assignment_claimed` | Expert claims case |
| `consensus_initiated` | Multi-expert review started |
| `consensus_opinion_added` | Expert submits opinion |
| `consensus_reached` | Majority verdict established |
| `resolution_submitted` | Resolution created |

### Governance
| Event | Trigger |
|---|---|
| `export_requested` | Data export created |
| `dataset_snapshot_created` | Snapshot taken |
| `user_role_changed` | Admin changes role |

---

## Event Replay

Events support replay via the `?since=` parameter:

```
GET /telemetry/events?since=2026-05-17T00:00:00Z&event_type=case_resolved
```

Returns all matching events from that timestamp forward.
Consumers can track their last-processed timestamp and resume from there.

---

## Storage Schema

```sql
audit_events (
  id UUID PRIMARY KEY,
  event_type TEXT NOT NULL,
  actor_id UUID → users.id (nullable),
  target_type TEXT NOT NULL,
  target_id UUID (nullable),
  event_metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
)
-- No updated_at — immutable
```

---

## Retention Policy

Current: events are retained indefinitely.

Future (Phase 7+):
- Archive events > 2 years to cold storage
- Maintain index for fast recent queries
- `event_metadata` may contain compressed details for older events

No events are deleted — only archived. The audit trail is permanent.

---

## Event Consumption Patterns

**Dashboard polling** (current): `GET /telemetry/events?limit=20`  
**Replay from checkpoint**: `GET /telemetry/events?since={last_processed_at}`  
**Case audit trail**: `GET /audit/cases/{case_id}`  
**Actor history**: `GET /telemetry/events?actor_id={user_id}`  

---

## Future: Message Broker Migration

When event volume justifies a real message broker:

1. Implement `KafkaPublisher` with the same `publish(event)` interface
2. Set `EVENT_BACKEND=kafka` in env
3. `event_publisher.py` routes to Kafka instead of PostgreSQL
4. Keep PostgreSQL as the durable audit log (dual-write)
5. Consumers read from Kafka for real-time processing

Zero changes required in routers or services.
