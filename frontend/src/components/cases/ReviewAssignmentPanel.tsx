"use client";

import { useState } from "react";
import { cn, formatRelativeTime } from "@/lib/utils";
import type { ReviewAssignment } from "@/lib/types";
import Button from "@/components/ui/Button";
import { reviews as reviewsApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { ClipboardList, CheckCircle2, Clock, ArrowRight } from "lucide-react";

const statusConfig: Record<string, { label: string; color: string }> = {
  pending: { label: "Pending", color: "text-amber-400" },
  claimed: { label: "Claimed", color: "text-blue-400" },
  in_review: { label: "In Review", color: "text-blue-400" },
  complete: { label: "Complete", color: "text-emerald-400" },
  transferred: { label: "Transferred", color: "text-zinc-400" },
  declined: { label: "Declined", color: "text-zinc-600" },
};

const typeConfig: Record<string, string> = {
  primary: "Primary Review",
  secondary: "Second Opinion",
  escalation: "Escalation Review",
};

interface ReviewAssignmentPanelProps {
  caseId: string;
  assignments: ReviewAssignment[];
  onUpdate: () => void;
}

export default function ReviewAssignmentPanel({
  caseId,
  assignments,
  onUpdate,
}: ReviewAssignmentPanelProps) {
  const { user } = useAuth();
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState("");

  if (!user || (user.role !== "expert" && user.role !== "admin")) return null;

  const myAssignment = assignments.find(
    (a) =>
      a.reviewer_username === user.username &&
      ["pending", "claimed", "in_review"].includes(a.status)
  );

  async function claimCase() {
    setClaiming(true);
    setError("");
    try {
      await reviewsApi.claim(caseId);
      onUpdate();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to claim");
    } finally {
      setClaiming(false);
    }
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-zinc-800 flex items-center gap-2">
        <ClipboardList className="h-4 w-4 text-amber-400" />
        <span className="text-sm font-semibold text-zinc-100">Review Assignments</span>
        <span className="ml-auto text-xs text-zinc-600">
          {assignments.length} assignment{assignments.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="p-4 flex flex-col gap-3">
        {assignments.length === 0 ? (
          <p className="text-xs text-zinc-600 italic">No review assignments yet.</p>
        ) : (
          assignments.map((a) => {
            const cfg = statusConfig[a.status] ?? { label: a.status, color: "text-zinc-400" };
            return (
              <div
                key={a.id}
                className={cn(
                  "flex items-start gap-2 py-2 px-3 rounded-lg",
                  a.reviewer_username === user.username
                    ? "bg-zinc-800/50 border border-zinc-700"
                    : "bg-zinc-800/20"
                )}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-zinc-300 font-medium">{a.reviewer_username}</span>
                    <span className={cn("font-medium", cfg.color)}>{cfg.label}</span>
                    <span className="text-zinc-600">{typeConfig[a.review_type] ?? a.review_type}</span>
                  </div>
                  {a.notes && (
                    <p className="text-xs text-zinc-500 mt-0.5 truncate">{a.notes}</p>
                  )}
                  <p className="text-xs text-zinc-700 mt-0.5">
                    {a.claimed_at ? `Claimed ${formatRelativeTime(a.claimed_at)}` : `Assigned ${formatRelativeTime(a.created_at)}`}
                  </p>
                </div>
                {a.status === "complete" && (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                )}
              </div>
            );
          })
        )}

        {/* Claim button if no active assignment for current user */}
        {!myAssignment && (
          <div>
            <Button
              variant="secondary"
              size="sm"
              onClick={claimCase}
              isLoading={claiming}
            >
              <ArrowRight className="h-3.5 w-3.5" />
              Claim for Review
            </Button>
            {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
          </div>
        )}
      </div>
    </div>
  );
}
