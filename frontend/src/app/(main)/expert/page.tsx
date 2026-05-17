"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { useAuth } from "@/contexts/AuthContext";
import { cases as casesApi, reviews as reviewsApi, expertProfiles } from "@/lib/api";
import CaseCard from "@/components/cases/CaseCard";
import { PageSpinner } from "@/components/ui/Spinner";
import ExpertProfileCard, { VerificationBadge } from "@/components/cases/ExpertProfileCard";
import { Shield, ClipboardList, PlusCircle } from "lucide-react";
import Button from "@/components/ui/Button";

export default function ExpertQueuePage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !user) router.push("/login?return=/expert");
    if (!authLoading && user && user.role === "user") router.push("/");
  }, [user, authLoading, router]);

  const { data: myProfile, isLoading: profileLoading } = useSWR(
    user && user.role !== "user" ? "expert-profile-me" : null,
    () => expertProfiles.getMe().catch(() => null)
  );

  const { data: queue, isLoading: queueLoading } = useSWR(
    user && user.role !== "user" ? "review-queue" : null,
    () => reviewsApi.queue()
  );

  const { data: openCases, isLoading: casesLoading } = useSWR(
    user && user.role !== "user" ? "expert-open-cases" : null,
    () => casesApi.list({ status: "expert_review", limit: 30 })
  );

  if (authLoading || !user) return <PageSpinner />;
  if (user.role === "user") return null;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-amber-400" />
          <h1 className="text-xl font-semibold text-zinc-100">Expert Dashboard</h1>
        </div>
        {!myProfile && !profileLoading && (
          <Button
            size="sm"
            variant="secondary"
            onClick={() => router.push("/expert/profile")}
          >
            <PlusCircle className="h-3.5 w-3.5" />
            Create Expert Profile
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Expert profile card */}
        <div className="lg:col-span-1">
          {myProfile ? (
            <ExpertProfileCard profile={myProfile} />
          ) : (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-center">
              <Shield className="h-8 w-8 mx-auto mb-2 text-zinc-700" />
              <p className="text-sm text-zinc-400 mb-1">No expert profile</p>
              <p className="text-xs text-zinc-600 mb-3">
                Create a profile to display your credentials and specializations.
              </p>
              <Button size="sm" onClick={() => router.push("/expert/profile")}>
                Create Profile
              </Button>
            </div>
          )}
        </div>

        {/* Queue */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          {/* My assignments */}
          {queue && queue.assigned.length > 0 && (
            <div>
              <h2 className="text-sm font-medium text-zinc-400 mb-2 flex items-center gap-1.5">
                <ClipboardList className="h-4 w-4" />
                My Assignments ({queue.assigned.length})
              </h2>
              <div className="flex flex-col gap-2">
                {queue.assigned.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => router.push(`/cases/${a.case_id}`)}
                    className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-xl p-3 flex items-center justify-between gap-3 cursor-pointer transition-colors"
                  >
                    <div>
                      <p className="text-sm text-zinc-300 font-medium">
                        Case {a.case_id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-zinc-600">
                        {a.review_type} review · {a.status}
                      </p>
                    </div>
                    <span className="text-xs text-amber-400 shrink-0">
                      {a.status === "pending" ? "Action needed" : "In progress"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Claimable cases */}
          {queueLoading && <PageSpinner />}

          {queue && queue.claimable.length > 0 && (
            <div>
              <h2 className="text-sm font-medium text-zinc-400 mb-2">
                Available to Claim ({queue.claimable.length})
              </h2>
              <div className="flex flex-col gap-2">
                {(queue.claimable as { id: string; title: string; status: string; setting: string | null; created_at: string }[]).map(
                  (c) => (
                    <div
                      key={c.id}
                      onClick={() => router.push(`/cases/${c.id}`)}
                      className="bg-zinc-900 border border-zinc-800 hover:border-amber-600 rounded-xl p-3 cursor-pointer transition-colors"
                    >
                      <p className="text-sm text-zinc-200 font-medium">{c.title}</p>
                      <p className="text-xs text-zinc-600 mt-0.5">
                        {c.setting ?? "Unknown setting"} · {c.created_at.slice(0, 10)}
                      </p>
                    </div>
                  )
                )}
              </div>
            </div>
          )}

          {/* All expert_review cases */}
          {!queueLoading && !casesLoading && openCases && (
            <div>
              <h2 className="text-sm font-medium text-zinc-400 mb-2">
                Expert Review Queue ({openCases.items.length})
              </h2>
              {openCases.items.length === 0 ? (
                <div className="text-center py-10 border border-zinc-800 rounded-xl text-zinc-500 text-sm">
                  <Shield className="h-8 w-8 mx-auto mb-2 text-zinc-700" />
                  No cases in expert review queue.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {openCases.items.map((c) => (
                    <CaseCard key={c.id} case_={c} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
