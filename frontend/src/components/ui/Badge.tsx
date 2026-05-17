import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "amber" | "blue" | "green" | "red" | "orange" | "zinc";
  className?: string;
}

export default function Badge({
  children,
  variant = "default",
  className,
}: BadgeProps) {
  const variants = {
    default: "bg-zinc-800 text-zinc-300 border border-zinc-700",
    amber: "bg-amber-900/50 text-amber-300 border border-amber-800",
    blue: "bg-blue-900/50 text-blue-300 border border-blue-800",
    green: "bg-emerald-900/50 text-emerald-300 border border-emerald-800",
    red: "bg-red-900/50 text-red-300 border border-red-800",
    orange: "bg-orange-900/50 text-orange-300 border border-orange-800",
    zinc: "bg-zinc-900 text-zinc-500 border border-zinc-800",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
