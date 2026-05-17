import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface MetricsCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  trend?: { value: number; label: string };
  icon?: ReactNode;
  highlight?: boolean;
  className?: string;
}

export default function MetricsCard({
  title,
  value,
  subtitle,
  trend,
  icon,
  highlight = false,
  className,
}: MetricsCardProps) {
  return (
    <div
      className={cn(
        "bg-zinc-900 border rounded-xl p-4 flex flex-col gap-1",
        highlight ? "border-amber-600/40" : "border-zinc-800",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-zinc-500">{title}</span>
        {icon && <span className="text-zinc-600">{icon}</span>}
      </div>
      <span
        className={cn(
          "text-2xl font-semibold",
          highlight ? "text-amber-400" : "text-zinc-100"
        )}
      >
        {typeof value === "number" ? value.toLocaleString() : value}
      </span>
      {subtitle && <span className="text-xs text-zinc-600">{subtitle}</span>}
      {trend && (
        <span
          className={cn(
            "text-xs font-medium",
            trend.value > 0
              ? "text-emerald-400"
              : trend.value < 0
              ? "text-red-400"
              : "text-zinc-500"
          )}
        >
          {trend.value > 0 ? "+" : ""}{trend.value}% {trend.label}
        </span>
      )}
    </div>
  );
}
