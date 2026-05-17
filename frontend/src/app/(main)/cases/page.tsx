"use client";

import { useState, useCallback } from "react";
import useSWR from "swr";
import { cases as casesApi } from "@/lib/api";
import CaseCard from "@/components/cases/CaseCard";
import { Input } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { PageSpinner } from "@/components/ui/Spinner";
import { Search, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CaseStatus, CaseSetting } from "@/lib/types";

const STATUSES: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "open", label: "Open" },
  { value: "under_review", label: "Under Review" },
  { value: "resolved", label: "Resolved" },
];

const SETTINGS: { value: string; label: string }[] = [
  { value: "", label: "All Settings" },
  { value: "daycare", label: "Daycare" },
  { value: "shelter", label: "Shelter" },
  { value: "home", label: "Home" },
  { value: "grooming", label: "Grooming" },
  { value: "vet", label: "Vet" },
  { value: "other", label: "Other" },
];

export default function CasesPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [setting, setSetting] = useState("");
  const [cursor, setCursor] = useState<string | undefined>();

  const params = {
    ...(search ? { search } : {}),
    ...(status ? { status } : {}),
    ...(setting ? { setting } : {}),
    ...(cursor ? { cursor } : {}),
    limit: 20,
  };

  const { data, isLoading, error } = useSWR(
    ["cases", params],
    () => casesApi.list(params),
    { keepPreviousData: true }
  );

  function resetFilters() {
    setSearch("");
    setStatus("");
    setSetting("");
    setCursor(undefined);
  }

  const activeFilters = !!(search || status || setting);

  return (
    <div className="flex flex-col gap-6">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-zinc-100">Case Library</h1>
          <p className="text-sm text-zinc-500 mt-0.5">
            Community-submitted canine behavioral incidents
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setCursor(undefined); }}
            placeholder="Search cases..."
            className="w-full h-9 pl-9 pr-3 text-sm bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-amber-500"
          />
        </div>

        <div className="flex gap-2 flex-wrap">
          {STATUSES.map((s) => (
            <button
              key={s.value}
              onClick={() => { setStatus(s.value); setCursor(undefined); }}
              className={cn(
                "px-3 h-9 text-xs rounded-lg border transition-colors",
                status === s.value
                  ? "bg-amber-400/10 border-amber-500 text-amber-300"
                  : "border-zinc-700 text-zinc-400 hover:border-zinc-600 hover:text-zinc-300"
              )}
            >
              {s.label}
            </button>
          ))}
        </div>

        <select
          value={setting}
          onChange={(e) => { setSetting(e.target.value); setCursor(undefined); }}
          className="h-9 px-2 text-sm bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-300 focus:outline-none focus:border-amber-500"
        >
          {SETTINGS.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>

        {activeFilters && (
          <Button variant="ghost" size="sm" onClick={resetFilters}>
            Clear
          </Button>
        )}
      </div>

      {/* Content */}
      {isLoading && <PageSpinner />}

      {error && (
        <div className="text-sm text-red-400 bg-red-950/30 border border-red-900 rounded-lg px-4 py-3">
          Failed to load cases. Is the backend running?
        </div>
      )}

      {data && (
        <>
          {data.items.length === 0 ? (
            <div className="text-center py-16 text-zinc-500">
              <p className="text-lg font-medium text-zinc-400 mb-2">No cases found</p>
              <p className="text-sm">
                {activeFilters ? "Try different filters" : "Be the first to submit a case"}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.items.map((c) => (
                <CaseCard key={c.id} case_={c} />
              ))}
            </div>
          )}

          {data.has_more && (
            <div className="flex justify-center pt-4">
              <Button
                variant="secondary"
                onClick={() => setCursor(data.next_cursor ?? undefined)}
              >
                Load more
              </Button>
            </div>
          )}

          <p className="text-xs text-zinc-600 text-center">
            {data.items.length} case{data.items.length !== 1 ? "s" : ""}
          </p>
        </>
      )}
    </div>
  );
}
