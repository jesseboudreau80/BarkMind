"use client";

import { useRouter } from "next/navigation";
import Card from "@/components/ui/Card";
import StatusBadge from "./StatusBadge";
import { CaseTagBadge } from "./TagBadge";
import { formatRelativeTime, formatSetting } from "@/lib/utils";
import type { CaseListItem } from "@/lib/types";
import { Eye, MessageSquare } from "lucide-react";

interface CaseCardProps {
  case_: CaseListItem;
  tags?: import("@/lib/types").CaseTag[];
}

export default function CaseCard({ case_, tags = [] }: CaseCardProps) {
  const router = useRouter();

  return (
    <Card
      hover
      onClick={() => router.push(`/cases/${case_.id}`)}
      className="p-4 flex flex-col gap-3"
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <StatusBadge status={case_.status} />
          {case_.setting && (
            <span className="text-xs text-zinc-500 font-mono">
              {formatSetting(case_.setting)}
            </span>
          )}
          {case_.subject_age_estimate && (
            <span className="text-xs text-zinc-600 capitalize">
              {case_.subject_age_estimate}
            </span>
          )}
        </div>
        <span className="text-xs text-zinc-600 whitespace-nowrap shrink-0">
          {formatRelativeTime(case_.created_at)}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-sm font-medium text-zinc-100 leading-snug line-clamp-2">
        {case_.title}
      </h3>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.slice(0, 4).map((ct) => (
            <CaseTagBadge key={ct.id} caseTag={ct} />
          ))}
          {tags.length > 4 && (
            <span className="text-xs text-zinc-600">+{tags.length - 4}</span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-zinc-600 pt-1 border-t border-zinc-800/60">
        <span>
          by{" "}
          <span
            className="text-zinc-400 hover:text-amber-400 cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              router.push(`/profile/${case_.submitter.username}`);
            }}
          >
            {case_.submitter.username}
          </span>
        </span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Eye className="h-3 w-3" />
            {case_.view_count}
          </span>
        </div>
      </div>
    </Card>
  );
}
