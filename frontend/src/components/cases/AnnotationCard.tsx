"use client";

import { useState } from "react";
import { cn, formatRelativeTime } from "@/lib/utils";
import type { Annotation } from "@/lib/types";
import Badge from "@/components/ui/Badge";
import ConfidenceBadge from "@/components/ui/ConfidenceBadge";
import { Shield, Clock, Tag, ChevronDown, ChevronUp, History } from "lucide-react";
import { annotations as annotationsApi } from "@/lib/api";

const typeConfig = {
  observation: { label: "Observation", variant: "blue" as const },
  interpretation: { label: "Interpretation", variant: "default" as const },
  concern: { label: "Concern", variant: "amber" as const },
  recommendation: { label: "Recommendation", variant: "green" as const },
};

// Marker type color for taxonomy category dots
const categoryColors: Record<string, string> = {
  body_posture: "bg-amber-400",
  tail_position: "bg-blue-400",
  ear_position: "bg-purple-400",
  eye_contact: "bg-cyan-400",
  mouth_tension: "bg-orange-400",
  stress_indicators: "bg-red-400",
  fear_indicators: "bg-red-500",
  play_signals: "bg-emerald-400",
  arousal_escalation: "bg-orange-500",
  social_engagement: "bg-teal-400",
  avoidance: "bg-yellow-400",
  resource_guarding: "bg-rose-400",
  handler_intervention: "bg-indigo-400",
  environmental_triggers: "bg-lime-400",
};

interface AnnotationCardProps {
  annotation: Annotation;
  onUpdate?: () => void;
}

export default function AnnotationCard({ annotation: a, onUpdate }: AnnotationCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [showRevisions, setShowRevisions] = useState(false);
  const [revisions, setRevisions] = useState<unknown[] | null>(null);

  const tc = typeConfig[a.annotation_type] ?? typeConfig.observation;

  async function loadRevisions(caseId: string) {
    if (revisions) {
      setShowRevisions((v) => !v);
      return;
    }
    try {
      // We need to derive caseId — it's not on the annotation object in this component
      // For now, use the annotation's extra_data or skip
      setShowRevisions(true);
    } catch {
      // pass
    }
  }

  return (
    <div
      className={cn(
        "rounded-lg border p-3 flex flex-col gap-2",
        a.is_expert
          ? "border-amber-800/50 bg-amber-950/15"
          : "border-zinc-800 bg-zinc-900/50"
      )}
    >
      {/* Header row */}
      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant={tc.variant}>{tc.label}</Badge>
        {a.is_expert && (
          <span className="flex items-center gap-1 text-xs text-amber-400 font-medium">
            <Shield className="h-3 w-3" />
            Expert
          </span>
        )}
        {a.confidence_level && (
          <ConfidenceBadge level={a.confidence_level} />
        )}
        {a.revision_count > 0 && (
          <span className="flex items-center gap-0.5 text-xs text-zinc-600" title="Edited">
            <History className="h-3 w-3" />
            {a.revision_count}
          </span>
        )}
        <span className="ml-auto text-xs text-zinc-600 shrink-0">
          {a.author_username} · {formatRelativeTime(a.created_at)}
        </span>
      </div>

      {/* Timestamp range */}
      {(a.timestamp_start != null || a.timestamp_end != null) && (
        <span className="flex items-center gap-1 text-xs text-zinc-500 font-mono">
          <Clock className="h-3 w-3" />
          {a.timestamp_start != null ? `${a.timestamp_start}s` : ""}
          {a.timestamp_end != null ? ` – ${a.timestamp_end}s` : ""}
        </span>
      )}

      {/* Taxonomy tags */}
      {a.taxonomy_refs.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {a.taxonomy_refs.map((ref) => {
            const dot = categoryColors[ref.term.category] ?? "bg-zinc-400";
            return (
              <span
                key={ref.id}
                className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-xs bg-zinc-800 border border-zinc-700 text-zinc-300 font-mono"
                title={ref.term.description ?? ref.term.category}
              >
                <span className={cn("w-1.5 h-1.5 rounded-full", dot)} />
                {ref.term.label}
              </span>
            );
          })}
        </div>
      )}

      {/* Body text */}
      <div
        className={cn(
          "text-sm text-zinc-200 leading-relaxed",
          !expanded && "line-clamp-3"
        )}
      >
        {a.body}
      </div>

      {/* Expand if body is long */}
      {a.body.length > 200 && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-zinc-600 hover:text-zinc-400 flex items-center gap-1 self-start"
        >
          {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          {expanded ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  );
}
