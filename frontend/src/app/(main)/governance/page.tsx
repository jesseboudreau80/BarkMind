"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { useAuth } from "@/contexts/AuthContext";
import { auditLog, reviews as reviewsApi } from "@/lib/api";
import MetricsCard from "@/components/governance/MetricsCard";
import TelemetryFeed from "@/components/governance/TelemetryFeed";
import { PageSpinner } from "@/components/ui/Spinner";
import {
  Shield,
  Activity,
  AlertTriangle,
  Lock,
  ClipboardList,
  Users,
  Database,
} from "lucide-react";
import Button from "@/components/ui/Button";

export default function GovernancePage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) router.push("/login?return=/governance");
    if (!authLoading && user && user.role !== "admin") router.push("/");
  }, [user, authLoading, router]);

  const { data: govSummary, isLoading: sumLoading } = useSWR(
    user?.role === "admin" ? "governance-summary" : null,
    () => auditLog.getGovernanceSummary() as Promise<{
      total_cases: number;
      total_annotations: number;
      expert_count: number;
      pending_assignments: number;
      case_status_distribution: Record<string, number>;
      recent_audit_events: unknown[];
    }>
  );

  const { data: opsData, isLoading: opsLoading } = useSWR(
    user?.role === "admin" ? "ops-overview" : null,
    async () => {
      const res = await fetch("/api-backend/telemetry/ops", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("barkmind_token") ?? ""}`,
        },
      });
      return res.json();
    }
  );

  if (authLoading || !user) return <PageSpinner />;
  if (user.role !== "admin") return null;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-amber-400" />
          <h1 className="text-xl font-semibold text-zinc-100">
            Governance Dashboard
          </h1>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => router.push("/analytics")}
          >
            <Activity className="h-3.5 w-3.5" />
            Full Analytics
          </Button>
        </div>
      </div>

      {/* Platform overview metrics */}
      {sumLoading ? (
        <PageSpinner />
      ) : govSummary ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MetricsCard
            title="Total Cases"
            value={govSummary.total_cases ?? 0}
            icon={<Database className="h-4 w-4" />}
          />
          <MetricsCard
            title="Annotations"
            value={govSummary.total_annotations ?? 0}
            icon={<ClipboardList className="h-4 w-4" />}
          />
          <MetricsCard
            title="Verified Experts"
            value={govSummary.expert_count ?? 0}
            icon={<Users className="h-4 w-4" />}
          />
          <MetricsCard
            title="Pending Reviews"
            value={govSummary.pending_assignments ?? 0}
            highlight={(govSummary.pending_assignments ?? 0) > 0}
            icon={<AlertTriangle className="h-4 w-4" />}
          />
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Operational attention panel */}
        {opsData && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              <h2 className="text-sm font-semibold text-zinc-200">
                Operational Status
              </h2>
              {opsData.attention_required && (
                <span className="ml-auto text-xs bg-amber-950/40 border border-amber-700 text-amber-300 px-2 py-0.5 rounded">
                  Action needed
                </span>
              )}
            </div>

            <div className="grid grid-cols-3 gap-3">
              {[
                { label: "Pending Assignments", value: opsData.pending_assignments, alert: opsData.pending_assignments > 0 },
                { label: "Open Consensus", value: opsData.open_consensus_reviews, alert: opsData.open_consensus_reviews > 0 },
                { label: "Escalated Cases", value: opsData.escalated_cases, alert: opsData.escalated_cases > 0 },
              ].map((item) => (
                <div
                  key={item.label}
                  className={`text-center py-2 rounded-lg ${
                    item.alert ? "bg-amber-950/20 border border-amber-800/40" : "bg-zinc-800/40"
                  }`}
                >
                  <p className={`text-lg font-semibold ${item.alert ? "text-amber-400" : "text-zinc-300"}`}>
                    {item.value}
                  </p>
                  <p className="text-xs text-zinc-600">{item.label}</p>
                </div>
              ))}
            </div>

            {/* Stale reviews */}
            {opsData.stale_reviews_count > 0 && (
              <div className="border-t border-zinc-800 pt-3">
                <p className="text-xs font-medium text-amber-400 mb-2">
                  Stale Reviews (&gt;7 days) — {opsData.stale_reviews_count}
                </p>
                <div className="flex flex-col gap-1.5">
                  {opsData.stale_reviews.slice(0, 5).map((r: { assignment_id: string; case_id: string; days_pending: number; review_type: string }) => (
                    <div
                      key={r.assignment_id}
                      onClick={() => router.push(`/cases/${r.case_id}`)}
                      className="flex items-center gap-2 text-xs text-zinc-400 hover:text-zinc-200 cursor-pointer"
                    >
                      <span className="font-mono text-zinc-600">
                        {r.case_id.slice(0, 8)}...
                      </span>
                      <span>{r.review_type}</span>
                      <span className="ml-auto text-amber-400">
                        {r.days_pending}d overdue
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Case status distribution */}
        {govSummary?.case_status_distribution && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-3">
            <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
              <Lock className="h-4 w-4 text-amber-400" />
              Case Status Distribution
            </h2>
            {Object.entries(govSummary.case_status_distribution)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([st, count]) => {
                const total = Object.values(govSummary.case_status_distribution).reduce(
                  (a: number, b) => a + (b as number), 0
                );
                const pct = total > 0 ? Math.round(((count as number) / total) * 100) : 0;
                return (
                  <div key={st} className="flex items-center gap-2 text-xs">
                    <span className="w-28 text-zinc-400 capitalize shrink-0">
                      {st.replace(/_/g, " ")}
                    </span>
                    <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-400 rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-zinc-600 w-8 text-right">{count as number}</span>
                  </div>
                );
              })}
          </div>
        )}
      </div>

      {/* Recent audit events */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="h-4 w-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-zinc-200">Recent Activity</h2>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto"
            onClick={() => router.push("/analytics")}
          >
            Full log →
          </Button>
        </div>
        <TelemetryFeed />
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "View Analytics", path: "/analytics", icon: <Activity className="h-4 w-4" /> },
          { label: "Expert Queue", path: "/expert", icon: <Shield className="h-4 w-4" /> },
          { label: "Moderation", path: "/moderation", icon: <Users className="h-4 w-4" /> },
        ].map((action) => (
          <button
            key={action.path}
            onClick={() => router.push(action.path)}
            className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl p-3 flex flex-col items-center gap-2 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            {action.icon}
            <span className="text-xs">{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
