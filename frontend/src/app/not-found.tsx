import Link from "next/link";
import { Dog } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center text-center px-4">
      <Dog className="h-12 w-12 text-zinc-700 mb-4" />
      <h1 className="text-3xl font-bold text-zinc-100 mb-2">404</h1>
      <p className="text-zinc-500 mb-6">This page doesn&apos;t exist or has been archived.</p>
      <Link
        href="/cases"
        className="text-sm text-amber-400 hover:underline"
      >
        Back to cases
      </Link>
    </div>
  );
}
