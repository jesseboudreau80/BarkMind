import Badge from "@/components/ui/Badge";
import type { Verdict } from "@/lib/types";

const config: Record<Verdict, { label: string; variant: "green" | "amber" | "orange" | "red" }> = {
  safe: { label: "Safe", variant: "green" },
  concern: { label: "Concern", variant: "amber" },
  escalation_risk: { label: "Escalation Risk", variant: "orange" },
  requires_intervention: { label: "Requires Intervention", variant: "red" },
};

export default function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const c = config[verdict] ?? { label: verdict, variant: "zinc" as const };
  return (
    <Badge variant={c.variant as "green" | "amber" | "orange" | "red"}>
      {c.label}
    </Badge>
  );
}
