import { cn } from "@/lib/utils";

interface BarChartProps {
  data: Record<string, number>;
  title?: string;
  color?: string;
  maxItems?: number;
  className?: string;
}

export default function BarChart({
  data,
  title,
  color = "bg-amber-400",
  maxItems = 10,
  className,
}: BarChartProps) {
  const entries = Object.entries(data)
    .sort(([, a], [, b]) => b - a)
    .slice(0, maxItems);

  const max = Math.max(...entries.map(([, v]) => v), 1);

  if (entries.length === 0) {
    return <p className="text-xs text-zinc-600 italic">No data</p>;
  }

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      {title && (
        <p className="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">
          {title}
        </p>
      )}
      {entries.map(([label, value]) => {
        const pct = (value / max) * 100;
        return (
          <div key={label} className="flex items-center gap-2 text-xs">
            <span className="w-32 text-zinc-400 truncate shrink-0 capitalize">
              {label.replace(/_/g, " ")}
            </span>
            <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all", color)}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-zinc-600 w-8 text-right shrink-0">{value}</span>
          </div>
        );
      })}
    </div>
  );
}
