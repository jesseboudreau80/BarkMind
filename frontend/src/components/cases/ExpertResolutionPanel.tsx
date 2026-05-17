import VerdictBadge from "./VerdictBadge";
import { formatDate } from "@/lib/utils";
import type { ExpertResolution } from "@/lib/types";
import { Shield } from "lucide-react";

export default function ExpertResolutionPanel({
  resolution,
}: {
  resolution: ExpertResolution;
}) {
  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-900/80">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800">
        <Shield className="h-4 w-4 text-amber-400" />
        <span className="text-sm font-semibold text-zinc-100">Expert Resolution</span>
      </div>

      <div className="p-4 flex flex-col gap-4">
        {/* Verdict */}
        <div className="flex items-center gap-3">
          <VerdictBadge verdict={resolution.verdict} />
          {resolution.confidence_level && (
            <span className="text-xs text-zinc-500">
              Confidence: <span className="text-zinc-400">{resolution.confidence_level}</span>
            </span>
          )}
          <span className="ml-auto text-xs text-zinc-600">
            by{" "}
            <span className="text-zinc-400">{resolution.expert_username}</span>
            {" · "}
            {formatDate(resolution.created_at)}
          </span>
        </div>

        {/* Summary */}
        <div>
          <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
            Expert Summary
          </p>
          <p className="text-sm text-zinc-200 leading-relaxed">{resolution.summary}</p>
        </div>

        {/* Recommendations */}
        {resolution.recommendations && (
          <div className="bg-zinc-800/60 rounded-lg p-3 border border-zinc-700/50">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
              Recommendations
            </p>
            <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">
              {resolution.recommendations}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
