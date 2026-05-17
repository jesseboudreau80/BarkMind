"use client";

import { useState, useCallback } from "react";
import { cn, formatRelativeTime } from "@/lib/utils";
import type { TimelineMarker, MarkerType } from "@/lib/types";
import { Shield, Plus, Trash2, MapPin } from "lucide-react";
import { timeline as timelineApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

// Color coding by marker type
const MARKER_COLORS: Record<MarkerType | string, string> = {
  trigger: "bg-yellow-400 border-yellow-400",
  escalation: "bg-red-400 border-red-400",
  de_escalation: "bg-emerald-400 border-emerald-400",
  handler_intervention: "bg-blue-400 border-blue-400",
  resolution: "bg-emerald-500 border-emerald-500",
  calming_signal: "bg-teal-400 border-teal-400",
  threshold_break: "bg-red-600 border-red-600",
  event: "bg-zinc-400 border-zinc-400",
  play_initiation: "bg-green-400 border-green-400",
  resource_guard: "bg-orange-400 border-orange-400",
};

const MARKER_LABELS: Record<MarkerType | string, string> = {
  trigger: "Trigger",
  escalation: "Escalation",
  de_escalation: "De-escalation",
  handler_intervention: "Handler",
  resolution: "Resolution",
  calming_signal: "Calming",
  threshold_break: "Threshold Break",
  event: "Event",
  play_initiation: "Play",
  resource_guard: "Resource Guard",
};

const MARKER_TYPES = [
  "event", "trigger", "escalation", "de_escalation",
  "handler_intervention", "calming_signal", "threshold_break",
  "resolution", "play_initiation", "resource_guard",
];

interface TimelineMarkersProps {
  caseId: string;
  mediaId?: string;
  duration?: number | null;
  initialMarkers?: TimelineMarker[];
  onMarkerClick?: (timestampSeconds: number) => void;
  onMarkersChange?: () => void;
}

export default function TimelineMarkers({
  caseId,
  mediaId,
  duration,
  initialMarkers = [],
  onMarkerClick,
  onMarkersChange,
}: TimelineMarkersProps) {
  const { user } = useAuth();
  const [markers, setMarkers] = useState<TimelineMarker[]>(initialMarkers);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addTs, setAddTs] = useState("");
  const [addLabel, setAddLabel] = useState("");
  const [addType, setAddType] = useState("event");
  const [addNotes, setAddNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const hasDuration = duration != null && duration > 0;

  async function addMarker() {
    const ts = parseFloat(addTs);
    if (isNaN(ts) || !addLabel.trim()) return;
    setSaving(true);
    try {
      const newMarker = await timelineApi.create(caseId, {
        timestamp_seconds: ts,
        label: addLabel.trim(),
        marker_type: addType,
        media_id: mediaId,
        notes: addNotes.trim() || undefined,
      });
      setMarkers((prev) => [...prev, newMarker].sort((a, b) => a.timestamp_seconds - b.timestamp_seconds));
      setAddTs("");
      setAddLabel("");
      setAddNotes("");
      setShowAddForm(false);
      onMarkersChange?.();
    } finally {
      setSaving(false);
    }
  }

  async function deleteMarker(markerId: string) {
    await timelineApi.delete(caseId, markerId);
    setMarkers((prev) => prev.filter((m) => m.id !== markerId));
    onMarkersChange?.();
  }

  if (markers.length === 0 && !user) return null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider flex items-center gap-1.5">
          <MapPin className="h-3.5 w-3.5 text-amber-400" />
          Behavioral Timeline
          {markers.length > 0 && (
            <span className="text-zinc-600 font-normal">({markers.length})</span>
          )}
        </h3>
        {user && (
          <button
            onClick={() => setShowAddForm((v) => !v)}
            className="text-xs text-zinc-500 hover:text-amber-400 flex items-center gap-1 transition-colors"
          >
            <Plus className="h-3 w-3" />
            Add marker
          </button>
        )}
      </div>

      {/* Timeline bar (shown when duration is known) */}
      {hasDuration && markers.length > 0 && (
        <div className="relative h-6 bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
          {/* Background track */}
          <div className="absolute inset-0 flex items-center">
            <div className="w-full h-0.5 bg-zinc-800" />
          </div>

          {/* Marker dots */}
          {markers.map((m) => {
            const pct = Math.min(99, Math.max(1, (m.timestamp_seconds / duration!) * 100));
            const color = MARKER_COLORS[m.marker_type] ?? MARKER_COLORS.event;
            return (
              <button
                key={m.id}
                onClick={() => onMarkerClick?.(m.timestamp_seconds)}
                onMouseEnter={() => setHoveredId(m.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={cn(
                  "absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full border-2 transition-transform hover:scale-150 cursor-pointer",
                  color
                )}
                style={{ left: `${pct}%` }}
                title={`${m.label} @ ${m.timestamp_seconds}s`}
                aria-label={m.label}
              />
            );
          })}
        </div>
      )}

      {/* Duration time axis labels */}
      {hasDuration && markers.length > 0 && (
        <div className="flex justify-between text-xs text-zinc-700 font-mono px-0.5">
          <span>0:00</span>
          <span>{Math.floor(duration! / 60)}:{Math.floor(duration! % 60).toString().padStart(2, "0")}</span>
        </div>
      )}

      {/* Marker list */}
      {markers.length > 0 && (
        <div className="flex flex-col gap-1">
          {markers.map((m) => {
            const color = MARKER_COLORS[m.marker_type] ?? MARKER_COLORS.event;
            const typeLabel = MARKER_LABELS[m.marker_type] ?? m.marker_type;
            const ts = m.timestamp_seconds;
            const tsFormatted = `${Math.floor(ts / 60)}:${Math.floor(ts % 60).toString().padStart(2, "0")}`;

            return (
              <div
                key={m.id}
                className="flex items-start gap-2 py-1.5 px-2 rounded-lg hover:bg-zinc-800/40 group transition-colors cursor-pointer"
                onClick={() => onMarkerClick?.(m.timestamp_seconds)}
              >
                <span className={cn("w-2 h-2 rounded-full mt-0.5 shrink-0", color.split(" ")[0])} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs font-mono text-amber-400/80">{tsFormatted}</span>
                    <span className="text-xs text-zinc-300 font-medium truncate">{m.label}</span>
                    <span className="text-xs text-zinc-600 shrink-0">[{typeLabel}]</span>
                    {m.is_expert && <Shield className="h-3 w-3 text-amber-400 shrink-0" />}
                  </div>
                  {m.notes && (
                    <p className="text-xs text-zinc-500 mt-0.5 truncate">{m.notes}</p>
                  )}
                </div>
                {user && m.author_username === user.username && (
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteMarker(m.id); }}
                    className="text-zinc-700 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all shrink-0"
                    aria-label="Delete marker"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add marker form */}
      {showAddForm && (
        <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-3 flex flex-col gap-2">
          <div className="flex gap-2 flex-wrap">
            <input
              type="number"
              value={addTs}
              onChange={(e) => setAddTs(e.target.value)}
              placeholder="Time (s)"
              step="0.1"
              min="0"
              className="w-24 h-8 px-2 text-xs bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-amber-500"
            />
            <select
              value={addType}
              onChange={(e) => setAddType(e.target.value)}
              className="h-8 px-2 text-xs bg-zinc-800 border border-zinc-700 rounded text-zinc-300 focus:outline-none focus:border-amber-500"
            >
              {MARKER_TYPES.map((t) => (
                <option key={t} value={t}>{MARKER_LABELS[t] ?? t}</option>
              ))}
            </select>
          </div>
          <input
            type="text"
            value={addLabel}
            onChange={(e) => setAddLabel(e.target.value)}
            placeholder="Label (e.g. 'Piloerection onset')"
            className="h-8 px-3 text-xs bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-amber-500"
          />
          <input
            type="text"
            value={addNotes}
            onChange={(e) => setAddNotes(e.target.value)}
            placeholder="Notes (optional)"
            className="h-8 px-3 text-xs bg-zinc-800 border border-zinc-700 rounded text-zinc-200 focus:outline-none focus:border-amber-500"
          />
          <div className="flex gap-2">
            <button
              onClick={addMarker}
              disabled={saving || !addLabel.trim() || !addTs}
              className="h-7 px-3 text-xs bg-amber-400 text-zinc-950 rounded font-medium disabled:opacity-50 hover:bg-amber-300 transition-colors"
            >
              {saving ? "Saving..." : "Add"}
            </button>
            <button
              onClick={() => setShowAddForm(false)}
              className="h-7 px-3 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
