import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hover?: boolean;
}

export default function Card({ children, className, onClick, hover }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-zinc-900 border border-zinc-800 rounded-xl",
        hover && "hover:border-zinc-700 hover:bg-zinc-900/80 cursor-pointer transition-colors",
        onClick && "cursor-pointer",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardSection({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("p-4 border-b border-zinc-800 last:border-b-0", className)}>
      {children}
    </div>
  );
}
