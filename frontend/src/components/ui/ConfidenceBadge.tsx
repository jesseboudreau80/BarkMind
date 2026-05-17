import { cn } from "@/lib/utils";

type Level = "high" | "medium" | "low" | null;

const config: Record<NonNullable<Level>, { label: string; color: string; dot: string }> = {
  high: {
    label: "High",
    color: "text-emerald-400 bg-emerald-950/40 border-emerald-800",
    dot: "bg-emerald-400",
  },
  medium: {
    label: "Medium",
    color: "text-amber-400 bg-amber-950/40 border-amber-800",
    dot: "bg-amber-400",
  },
  low: {
    label: "Low",
    color: "text-zinc-400 bg-zinc-800/40 border-zinc-700",
    dot: "bg-zinc-400",
  },
};

interface ConfidenceBadgeProps {
  level: Level;
  showLabel?: boolean;
  className?: string;
}

export default function ConfidenceBadge({
  level,
  showLabel = true,
  className,
}: ConfidenceBadgeProps) {
  if (!level) return null;
  const c = config[level];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium border",
        c.color,
        className
      )}
      title={`Confidence: ${c.label}`}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", c.dot)} />
      {showLabel && c.label}
    </span>
  );
}
