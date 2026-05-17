"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { useAuth } from "@/contexts/AuthContext";
import MetricsCard from "@/components/governance/MetricsCard";
import BarChart from "@/components/governance/BarChart";
import { PageSpinner } from "@/components/ui/Spinner";
import { Activity, Tag, Users, MessageSquare, GitMerge, Database } from "lucide-react";

type AnalyticsSummary = {
  generated_at: string;
  metrics: {
    totals: {
      cases: number;
      users: number;
      annotations: number;
      media_files: number;
      locked_cases: number;
      pending_reviews: number;
    };
    activity: {
      active_users_24h: number;
      events_last_7d: number;
      top_event_types_7d: Record<string, number>;
    };
  };
  cases: {
    total_cases: number;
    resolution_rate_pct: number;
    velocity_last_7_days: number;
    velocity_change_pct: number;
    status_distribution: Record<string, number>;
    setting_distribution: Record<string, number>;
    avg_resolution_hours: number | null;
  };
  annotations: {
    total_annotations: number;
    expert_annotations: number;
    expert_pct: number;
    with_taxonomy_refs: number;
    taxonomy_adoption_pct: number;
    type_distribution: Record<string, number>;
    confidence_distribution: Record<string, number>;
    top_taxonomy_terms: { slug: string; label: string; category: string; count: number }[];
  };
  experts: {
    total_experts: number;
    verified_experts: number;
    total_resolutions: number;
    pending_assignments: number;
    stale_assignments_7d: number;
    top_experts: { username: string; review_count: number; reputation_score: number; verified: boolean }[];
  };
  taxonomy: {
    total_terms: number;
    active_terms: number;
    total_category_refs: number;
    category_usage: Record<string, number>;
    unused_term_count: number;
  };
  consensus: {
    total_consensus_reviews: number;
    reached: number;
    disputed: number;
    agreement_rate_pct: number;
    avg_opinions_per_consensus: number;
    verdict_distribution: Record<string, number>;
  };
};

export default function AnalyticsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) router.push("/login?return=/analytics");
    if (!authLoading && user && user.role !== "admin") router.push("/");
  }, [user, authLoading, router]);

  const { data, isLoading } = useSWR<AnalyticsSummary>(
    user?.role === "admin" ? "analytics-summary" : null,
    async () => {
      const res = await fetch("/api-backend/analytics/summary", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("barkmind_token") ?? ""}`,
        },
      });
      return res.json();
    }
  );

  if (authLoading || !user) return <PageSpinner />;
  if (user.role !== "admin") return null;
  if (isLoading || !data) return <PageSpinner />;

  const { cases, annotations, experts, taxonomy, consensus, metrics } = data;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-2">
        <Activity className="h-5 w-5 text-amber-400" />
        <h1 className="text-xl font-semibold text-zinc-100">Platform Analytics</h1>
        <span className="ml-auto text-xs text-zinc-600">
          Generated {new Date(data.generated_at).toLocaleString()}
        </span>
      </div>

      {/* Platform totals */}
      <div>
        <h2 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">
          Platform Totals
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <MetricsCard title="Cases" value={metrics.totals.cases} icon={<Database className="h-4 w-4" />} />
          <MetricsCard title="Annotations" value={metrics.totals.annotations} icon={<MessageSquare className="h-4 w-4" />} />
          <MetricsCard title="Users" value={metrics.totals.users} icon={<Users className="h-4 w-4" />} />
          <MetricsCard title="Media Files" value={metrics.totals.media_files} />
          <MetricsCard title="Locked Cases" value={metrics.totals.locked_cases} icon={<Database className="h-4 w-4" />} />
          <MetricsCard title="Active (24h)" value={metrics.activity.active_users_24h} highlight={metrics.activity.active_users_24h > 0} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Case analytics */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Database className="h-4 w-4 text-amber-400" />
            Case Intelligence
          </h2>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-xl font-semibold text-zinc-100">{cases.resolution_rate_pct}%</p>
              <p className="text-xs text-zinc-600">Resolution Rate</p>
            </div>
            <div>
              <p className="text-xl font-semibold text-zinc-100">{cases.velocity_last_7_days}</p>
              <p className="text-xs text-zinc-600">Cases (7d)</p>
            </div>
            <div>
              <p className="text-xl font-semibold text-zinc-100">
                {cases.avg_resolution_hours != null ? `${cases.avg_resolution_hours}h` : "—"}
              </p>
              <p className="text-xs text-zinc-600">Avg Resolution</p>
            </div>
          </div>
          <BarChart data={cases.status_distribution} title="Status Distribution" />
          <BarChart data={cases.setting_distribution} title="Setting Distribution" color="bg-blue-400" />
        </div>

        {/* Annotation analytics */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-amber-400" />
            Annotation Intelligence
          </h2>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-xl font-semibold text-zinc-100">{annotations.expert_pct}%</p>
              <p className="text-xs text-zinc-600">Expert Authored</p>
            </div>
            <div>
              <p className="text-xl font-semibold text-zinc-100">{annotations.taxonomy_adoption_pct}%</p>
              <p className="text-xs text-zinc-600">Taxonomy Adoption</p>
            </div>
            <div>
              <p className="text-xl font-semibold text-zinc-100">{annotations.with_taxonomy_refs}</p>
              <p className="text-xs text-zinc-600">With Taxonomy</p>
            </div>
          </div>
          <BarChart data={annotations.type_distribution} title="Annotation Types" color="bg-blue-400" />
          <BarChart data={annotations.confidence_distribution} title="Confidence Levels" color="bg-emerald-400" />
        </div>

        {/* Taxonomy heatmap */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Tag className="h-4 w-4 text-amber-400" />
            Taxonomy Adoption
          </h2>
          <div className="grid grid-cols-3 gap-2 text-center text-sm mb-2">
            <div>
              <p className="font-semibold text-zinc-100">{taxonomy.active_terms}</p>
              <p className="text-xs text-zinc-600">Active Terms</p>
            </div>
            <div>
              <p className="font-semibold text-zinc-100">{taxonomy.total_category_refs}</p>
              <p className="text-xs text-zinc-600">Total References</p>
            </div>
            <div>
              <p className="font-semibold text-amber-400">{taxonomy.unused_term_count}</p>
              <p className="text-xs text-zinc-600">Unused Terms</p>
            </div>
          </div>
          <BarChart data={taxonomy.category_usage} title="Usage by Category" color="bg-purple-400" />

          {/* Top taxonomy terms */}
          {annotations.top_taxonomy_terms.length > 0 && (
            <div className="border-t border-zinc-800 pt-3">
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Top 10 Terms</p>
              <div className="flex flex-col gap-1">
                {annotations.top_taxonomy_terms.slice(0, 10).map((term) => (
                  <div key={term.slug} className="flex items-center gap-2 text-xs">
                    <span className="w-32 text-zinc-400 truncate font-mono">{term.label}</span>
                    <div className="flex-1 h-1 bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-400 rounded-full"
                        style={{
                          width: `${(term.count / (annotations.top_taxonomy_terms[0]?.count || 1)) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-zinc-600 w-6 text-right">{term.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Expert + Consensus */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-4">
          <h2 className="text-sm font-semibold text-zinc-200 flex items-center gap-2">
            <Users className="h-4 w-4 text-amber-400" />
            Expert &amp; Consensus
          </h2>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <p className="text-xl font-semibold text-zinc-100">{experts.verified_experts}</p>
              <p className="text-xs text-zinc-600">Verified Experts</p>
            </div>
            <div>
              <p className="text-xl font-semibold text-zinc-100">{experts.total_resolutions}</p>
              <p className="text-xs text-zinc-600">Resolutions</p>
            </div>
            <div>
              <p className="text-xl font-semibold text-zinc-100">{experts.stale_assignments_7d}</p>
              <p className="text-xs text-zinc-600 text-amber-400">Stale (7d)</p>
            </div>
          </div>

          {/* Top experts */}
          {experts.top_experts.length > 0 && (
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">Top Experts</p>
              <div className="flex flex-col gap-1.5">
                {experts.top_experts.slice(0, 5).map((e) => (
                  <div key={e.username} className="flex items-center gap-2 text-xs">
                    <span className="text-zinc-300 font-medium w-24 truncate">{e.username}</span>
                    {e.verified && (
                      <span className="text-emerald-400 text-xs">✓</span>
                    )}
                    <span className="text-zinc-600">{e.review_count} reviews</span>
                    <span className="ml-auto text-amber-400">{e.reputation_score} rep</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border-t border-zinc-800 pt-3">
            <div className="grid grid-cols-2 gap-3 text-center">
              <div>
                <p className="text-xl font-semibold text-emerald-400">{consensus.agreement_rate_pct}%</p>
                <p className="text-xs text-zinc-600">Consensus Agreement Rate</p>
              </div>
              <div>
                <p className="text-xl font-semibold text-zinc-100">{consensus.total_consensus_reviews}</p>
                <p className="text-xs text-zinc-600">Total Consensus Reviews</p>
              </div>
            </div>
            <BarChart
              data={consensus.verdict_distribution}
              title="Consensus Verdicts"
              color="bg-teal-400"
              className="mt-3"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
