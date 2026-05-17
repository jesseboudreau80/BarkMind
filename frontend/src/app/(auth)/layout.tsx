import Link from "next/link";
import { Dog } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-zinc-950 px-4">
      <div className="mb-8 flex flex-col items-center gap-2">
        <Link href="/" className="flex items-center gap-2 text-zinc-100 hover:text-amber-400 transition-colors">
          <Dog className="h-7 w-7 text-amber-400" />
          <span className="text-xl font-semibold tracking-tight">BarkMind</span>
        </Link>
        <p className="text-xs text-zinc-500">Canine Behavioral Intelligence Platform</p>
      </div>
      <div className="w-full max-w-sm">
        {children}
      </div>
    </div>
  );
}
