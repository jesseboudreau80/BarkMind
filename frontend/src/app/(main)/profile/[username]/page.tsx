"use client";

import { use } from "react";
import useSWR from "swr";
import { users as usersApi, cases as casesApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { PageSpinner } from "@/components/ui/Spinner";
import CaseCard from "@/components/cases/CaseCard";
import { User, Calendar, Star } from "lucide-react";

export default function ProfilePage({
  params,
}: {
  params: Promise<{ username: string }>;
}) {
  const { username } = use(params);

  const { data: profile, isLoading, error } = useSWR(
    `profile:${username}`,
    () => usersApi.profile(username)
  );

  const { data: casesData } = useSWR(
    profile ? `profile-cases:${username}` : null,
    () => casesApi.list({ limit: 20 })
  );

  const userCases = casesData?.items.filter(
    (c) => c.submitter.username === username
  ) ?? [];

  if (isLoading) return <PageSpinner />;

  if (error || !profile) {
    return (
      <div className="text-center py-16 text-zinc-500">
        <User className="h-10 w-10 mx-auto mb-3 text-zinc-700" />
        <p className="font-medium text-zinc-400">User not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      {/* Profile header */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 flex items-start gap-4">
        <div className="w-14 h-14 rounded-full bg-amber-400/20 flex items-center justify-center text-2xl font-bold text-amber-400 uppercase shrink-0">
          {profile.username[0]}
        </div>
        <div className="flex flex-col gap-1 flex-1">
          <h1 className="text-xl font-semibold text-zinc-100">
            {profile.display_name ?? profile.username}
          </h1>
          {profile.display_name && (
            <p className="text-sm text-zinc-500">@{profile.username}</p>
          )}
          {profile.bio && (
            <p className="text-sm text-zinc-400 mt-2">{profile.bio}</p>
          )}
          <div className="flex items-center gap-4 mt-3 text-xs text-zinc-500">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              Joined {formatDate(profile.created_at)}
            </span>
            <span className="flex items-center gap-1">
              <Star className="h-3 w-3" />
              {profile.reputation_score} reputation
            </span>
            <span>{profile.case_count} case{profile.case_count !== 1 ? "s" : ""}</span>
          </div>
        </div>
      </div>

      {/* Cases */}
      <div>
        <h2 className="text-sm font-medium text-zinc-400 mb-3">Submitted Cases</h2>
        {userCases.length === 0 ? (
          <div className="text-center py-8 border border-zinc-800 rounded-xl text-zinc-500 text-sm">
            No cases submitted yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {userCases.map((c) => (
              <CaseCard key={c.id} case_={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
