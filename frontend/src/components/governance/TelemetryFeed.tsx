"use client";

import { useEffect, useState } from "react";
import { formatRelativeTime } from "@/lib/utils";
import type { AuditEvent } from "@/lib/types";
import { auditLog } from "@/lib/api";
import Spinner from "@/components/ui/Spinner";
import { Activity } from "lucide-react";

const EVENT_COLORS: Record<string, string> = {
  case_created: "text-blue-400",
  case_resolved: "text-emerald-400",
  case_locked: "text-zinc-400",
  case_escalated: "text-orange-400",
  consensus_reached: "text-emerald-400",
  consensus_initiated: "text-blue-400",
  expert_verified: "text-amber-400",
  resolution_submitted: "text-emerald-400",
  export_requested: "text-purple-400",
  dataset_snapshot_created: "text-cyan-400",
};

export default function TelemetryFeed({ caseId }: { caseId?: string }) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const result = caseId
          ? await auditLog.getCaseAudit(caseId)
          : (await auditLog.getGovernanceSummary() as { recent_audit_events: AuditEvent[] })
              .recent_audit_events;
        setEvents(result as AuditEvent[]);
      } catch {
        // silent
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [caseId]);

  if (loading) return <div className="flex justify-center py-4"><Spinner size="sm" /></div>;

  return (
    <div className="flex flex-col gap-1">
      {events.length === 0 ? (
        <p className="text-xs text-zinc-600 italic py-2">No events yet.</p>
      ) : (
        events.map((e) => {
          const color = EVENT_COLORS[e.event_type] ?? "text-zinc-400";
          return (
            <div key={e.id} className="flex items-start gap-2 py-1 text-xs">
              <span className={`font-mono shrink-0 ${color}`}>
                {e.event_type.replace(/_/g, " ")}
              </span>
              <span className="text-zinc-600">
                {e.actor && <>by {e.actor} · </>}
                {formatRelativeTime(e.created_at)}
              </span>
            </div>
          );
        })
      )}
    </div>
  );
}
