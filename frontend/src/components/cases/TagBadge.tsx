import { cn, severityColor } from "@/lib/utils";
import type { CaseTag, Tag } from "@/lib/types";

const confidenceStyle = {
  observed: "opacity-100",
  probable: "opacity-75",
  possible: "opacity-50",
};

export function TagBadge({ tag }: { tag: Tag }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono",
        "bg-zinc-800 border border-zinc-700 text-zinc-300"
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full bg-current", severityColor(tag.severity_hint))} />
      {tag.label}
    </span>
  );
}

export function CaseTagBadge({ caseTag }: { caseTag: CaseTag }) {
  const conf = caseTag.confidence ?? "observed";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono",
        "bg-zinc-800 border border-zinc-700 text-zinc-300",
        confidenceStyle[conf as keyof typeof confidenceStyle] ?? "opacity-100"
      )}
      title={`Confidence: ${conf}${caseTag.timestamp_note ? ` — ${caseTag.timestamp_note}` : ""}`}
    >
      <span
        className={cn(
          "w-1.5 h-1.5 rounded-full bg-current",
          severityColor(caseTag.tag.severity_hint)
        )}
      />
      {caseTag.tag.label}
      {caseTag.confidence && caseTag.confidence !== "observed" && (
        <span className="text-zinc-500 text-[10px]">({caseTag.confidence[0]})</span>
      )}
    </span>
  );
}
