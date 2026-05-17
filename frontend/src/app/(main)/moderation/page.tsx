"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { PageSpinner } from "@/components/ui/Spinner";
import { Shield } from "lucide-react";

export default function ModerationPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.push("/login?return=/moderation");
    if (!isLoading && user && user.role !== "admin") router.push("/");
  }, [user, isLoading, router]);

  if (isLoading || !user) return <PageSpinner />;
  if (user.role !== "admin") return null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2">
        <Shield className="h-5 w-5 text-amber-400" />
        <h1 className="text-xl font-semibold text-zinc-100">Moderation</h1>
      </div>
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center text-zinc-500">
        <Shield className="h-8 w-8 mx-auto mb-3 text-zinc-700" />
        <p className="text-sm font-medium text-zinc-400 mb-1">Admin moderation panel</p>
        <p className="text-xs">
          User management, case moderation, and tag administration — coming in Phase 5.
        </p>
      </div>
    </div>
  );
}
