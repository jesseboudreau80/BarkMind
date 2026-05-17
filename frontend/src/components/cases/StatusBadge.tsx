import Badge from "@/components/ui/Badge";
import type { CaseStatus } from "@/lib/types";
import { Lock } from "lucide-react";

const config: Record<
  CaseStatus,
  { label: string; variant: "blue" | "amber" | "green" | "zinc" | "red" | "orange" }
> = {
  intake: { label: "Intake", variant: "zinc" },
  open: { label: "Open", variant: "blue" },
  under_review: { label: "Under Review", variant: "amber" },
  expert_review: { label: "Expert Review", variant: "amber" },
  consensus_pending: { label: "Consensus", variant: "orange" },
  escalated: { label: "Escalated", variant: "red" },
  resolved: { label: "Resolved", variant: "green" },
  locked: { label: "Locked", variant: "zinc" },
  archived: { label: "Archived", variant: "zinc" },
};

export default function StatusBadge({ status }: { status: CaseStatus }) {
  const c = config[status] ?? { label: status, variant: "zinc" as const };
  return (
    <Badge variant={c.variant}>
      {status === "locked" && <Lock className="h-2.5 w-2.5 mr-0.5" />}
      {c.label}
    </Badge>
  );
}
