"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { useAuth } from "@/contexts/AuthContext";
import { cases as casesApi } from "@/lib/api";
import CaseCard from "@/components/cases/CaseCard";
import Button from "@/components/ui/Button";
import { PageSpinner } from "@/components/ui/Spinner";
import { PlusCircle, Shield } from "lucide-react";

export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) router.push("/login?return=/dashboard");
  }, [user, authLoading, router]);

  const { data, isLoading } = useSWR(
    user ? ["cases-mine", user.username] : null,
    () => casesApi.list({ limit: 20 })
  );

  if (authLoading || !user) return <PageSpinner />;

  const myCases = data?.items.filter((c) => c.submitter.username === user.username) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-zinc-100">Dashboard</h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Welcome back,{" "}
            <span className="text-zinc-300">{user.display_name ?? user.username}</span>
          </p>
        </div>
        <Button onClick={() => router.push("/upload")}>
          <PlusCircle className="h-4 w-4" />
          Submit Case
        </Button>
      </div>

      {/* Role badge */}
      {(user.role === "expert" || user.role === "admin") && (
        <div className="flex items-center gap-2 bg-amber-950/30 border border-amber-800/40 rounded-xl px-4 py-3">
          <Shield className="h-4 w-4 text-amber-400" />
          <span className="text-sm text-amber-300">
            You have{" "}
            <span className="font-medium">{user.role}</span> access.{" "}
            <a href="/expert" className="underline hover:no-underline">
              View expert queue
            </a>
          </span>
        </div>
      )}

      {/* My cases */}
      <div>
        <h2 className="text-sm font-medium text-zinc-400 mb-3">My Cases</h2>
        {isLoading && <PageSpinner />}
        {myCases.length === 0 && !isLoading && (
          <div className="text-center py-10 border border-zinc-800 rounded-xl text-zinc-500">
            <p className="text-sm">You haven&apos;t submitted any cases yet.</p>
            <Button
              variant="secondary"
              className="mt-4"
              onClick={() => router.push("/upload")}
            >
              Submit your first case
            </Button>
          </div>
        )}
        {myCases.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {myCases.map((c) => (
              <CaseCard key={c.id} case_={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
