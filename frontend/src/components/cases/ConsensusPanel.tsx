"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { consensus as consensusApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import Button from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Input";
import VerdictBadge from "./VerdictBadge";
import type { Verdict } from "@/lib/types";
import { Users, ChevronDown, ChevronUp } from "lucide-react";

interface ConsensusData {
  id: string;
  case_id: string;
  status: string;
  initiated_by_username: string;
  verdict_tally: Record<string, number>;
  consensus_verdict: string | null;
  consensus_confidence: string | null;
  notes: string | null;
  opinion_count: number;
  opinions: {
    id: string;
    expert_username: string;
    verdict: string;
    confidence_level: string | null;
    summary: string | null;
    created_at: string;
  }[];
}

const VERDICTS = [
  { value: "safe", label: "Safe" },
  { value: "concern", label: "Concern" },
  { value: "escalation_risk", label: "Escalation Risk" },
  { value: "requires_intervention", label: "Requires Intervention" },
];

const statusColors: Record<string, string> = {
  open: "text-blue-400",
  reached: "text-emerald-400",
  disputed: "text-red-400",
  escalated: "text-orange-400",
};

export default function ConsensusPanel({
  caseId,
  initialData,
  onUpdate,
}: {
  caseId: string;
  initialData: ConsensusData | null;
  onUpdate: () => void;
}) {
  const { user } = useAuth();
  const [data, setData] = useState<ConsensusData | null>(initialData);
  const [showOpinions, setShowOpinions] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [selectedVerdict, setSelectedVerdict] = useState("");
  const [confidence, setConfidence] = useState("");
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");

  const isExpert = user && (user.role === "expert" || user.role === "admin");
  const hasOpinion = data?.opinions.some((o) => o.expert_username === user?.username);

  async function submitOpinion() {
    if (!selectedVerdict || !data) return;
    setSubmitting(true);
    setError("");
    try {
      const result = await consensusApi.submitOpinion(caseId, {
        verdict: selectedVerdict,
        confidence_level: confidence || undefined,
        summary: summary || undefined,
      });
      // Update local tally
      setData((prev) =>
        prev
          ? {
              ...prev,
              verdict_tally: result.current_tally,
              status: result.consensus_status,
              consensus_verdict: result.consensus_verdict,
            }
          : prev
      );
      setShowForm(false);
      onUpdate();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to submit opinion");
    } finally {
      setSubmitting(false);
    }
  }

  if (!data) {
    if (!isExpert) return null;
    return (
      <div className="text-xs text-zinc-600 italic">
        No consensus review initiated.
        {/* Initiation handled via admin action — not in the card UI */}
      </div>
    );
  }

  const total = Object.values(data.verdict_tally).reduce((a, b) => a + b, 0);
  const statusColor = statusColors[data.status] ?? "text-zinc-400";

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-800 flex items-center gap-2">
        <Users className="h-4 w-4 text-amber-400" />
        <span className="text-sm font-semibold text-zinc-100">Consensus Review</span>
        <span className={cn("text-xs font-medium ml-1", statusColor)}>
          [{data.status}]
        </span>
        {data.consensus_verdict && (
          <VerdictBadge verdict={data.consensus_verdict as Verdict} />
        )}
        <span className="ml-auto text-xs text-zinc-600">
          {data.opinion_count} opinion{data.opinion_count !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="p-4 flex flex-col gap-4">
        {/* Verdict tally bar */}
        {total > 0 && (
          <div className="flex flex-col gap-2">
            {Object.entries(data.verdict_tally)
              .filter(([, count]) => count > 0)
              .sort(([, a], [, b]) => b - a)
              .map(([verdict, count]) => {
                const pct = (count / total) * 100;
                return (
                  <div key={verdict} className="flex items-center gap-2 text-xs">
                    <span className="w-32 text-zinc-400 shrink-0 capitalize">
                      {verdict.replace(/_/g, " ")}
                    </span>
                    <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-400 rounded-full transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-zinc-500 w-12 text-right">
                      {count}/{total}
                    </span>
                  </div>
                );
              })}
          </div>
        )}

        {data.notes && (
          <p className="text-xs text-zinc-500 italic">{data.notes}</p>
        )}

        {/* Opinion list (collapsible) */}
        {data.opinions.length > 0 && (
          <div>
            <button
              onClick={() => setShowOpinions((v) => !v)}
              className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1"
            >
              {showOpinions ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
              {showOpinions ? "Hide" : "Show"} expert opinions
            </button>

            {showOpinions && (
              <div className="mt-2 flex flex-col gap-2">
                {data.opinions.map((op) => (
                  <div
                    key={op.id}
                    className="bg-zinc-800/50 rounded-lg p-2.5 flex flex-col gap-1"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-zinc-300">
                        {op.expert_username}
                      </span>
                      <VerdictBadge verdict={op.verdict as Verdict} />
                      {op.confidence_level && (
                        <span className="text-xs text-zinc-500">
                          ({op.confidence_level} confidence)
                        </span>
                      )}
                    </div>
                    {op.summary && (
                      <p className="text-xs text-zinc-400">{op.summary}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Submit opinion (expert only, not already submitted, consensus open) */}
        {isExpert && data.status === "open" && !hasOpinion && (
          <div>
            {!showForm ? (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowForm(true)}
              >
                Submit Opinion
              </Button>
            ) : (
              <div className="flex flex-col gap-2 border border-zinc-700 rounded-lg p-3">
                <p className="text-xs font-medium text-zinc-400">Your verdict:</p>
                <div className="flex flex-wrap gap-1.5">
                  {VERDICTS.map((v) => (
                    <button
                      key={v.value}
                      onClick={() => setSelectedVerdict(v.value)}
                      className={cn(
                        "px-2 py-1 rounded text-xs border transition-colors",
                        selectedVerdict === v.value
                          ? "bg-amber-400/10 border-amber-500 text-amber-300"
                          : "border-zinc-700 text-zinc-400 hover:border-zinc-600"
                      )}
                    >
                      {v.label}
                    </button>
                  ))}
                </div>
                <select
                  value={confidence}
                  onChange={(e) => setConfidence(e.target.value)}
                  className="h-7 px-2 text-xs bg-zinc-800 border border-zinc-700 rounded text-zinc-300 focus:outline-none focus:border-amber-500"
                >
                  <option value="">Confidence (optional)</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                <Textarea
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  placeholder="Brief summary (optional)"
                  className="min-h-[60px] text-xs"
                />
                {error && <p className="text-xs text-red-400">{error}</p>}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={submitOpinion}
                    isLoading={submitting}
                    disabled={!selectedVerdict}
                  >
                    Submit
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowForm(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {hasOpinion && (
          <p className="text-xs text-zinc-600 italic">
            You have submitted your opinion for this consensus.
          </p>
        )}
      </div>
    </div>
  );
}
