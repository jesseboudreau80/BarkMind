"use client";

import useSWR from "swr";
import { tags as tagsApi } from "@/lib/api";
import { TagBadge } from "@/components/cases/TagBadge";
import { PageSpinner } from "@/components/ui/Spinner";
import { severityLabel, severityColor } from "@/lib/utils";
import type { TagCategory } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<TagCategory, string> = {
  body_language: "Body Language",
  vocalization: "Vocalization",
  posture: "Posture",
  interaction: "Interaction",
  context: "Context",
};

const CATEGORY_DESC: Record<TagCategory, string> = {
  body_language: "Physical signals expressed through body position, coat, eyes, and tail",
  vocalization: "Auditory behavioral signals",
  posture: "Overall body stance and positioning relative to others",
  interaction: "Behaviors directed at other dogs or humans",
  context: "Environmental and situational factors",
};

export default function TagsPage() {
  const { data, isLoading } = useSWR("tags", tagsApi.list);

  if (isLoading) return <PageSpinner />;
  if (!data) return null;

  const totalTags = Object.values(data.categories).flat().length;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-xl font-semibold text-zinc-100 mb-1">
          Behavioral Tag Library
        </h1>
        <p className="text-sm text-zinc-500">
          {totalTags} curated behavioral descriptors across{" "}
          {Object.keys(data.categories).length} categories
        </p>
      </div>

      {(Object.entries(data.categories) as [TagCategory, typeof data.categories[TagCategory]][]).map(
        ([cat, catTags]) => (
          <div key={cat}>
            <div className="mb-3">
              <h2 className="text-base font-medium text-zinc-200">
                {CATEGORY_LABELS[cat]}
              </h2>
              <p className="text-xs text-zinc-600 mt-0.5">{CATEGORY_DESC[cat]}</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {catTags.map((tag) => (
                <div
                  key={tag.slug}
                  className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 flex flex-col gap-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <TagBadge tag={tag} />
                    <span
                      className={cn(
                        "text-xs font-mono",
                        severityColor(tag.severity_hint)
                      )}
                    >
                      {severityLabel(tag.severity_hint)}
                    </span>
                  </div>
                  {tag.description && (
                    <p className="text-xs text-zinc-500 leading-relaxed">
                      {tag.description}
                    </p>
                  )}
                  <p className="text-xs text-zinc-700 font-mono">{tag.slug}</p>
                </div>
              ))}
            </div>
          </div>
        )
      )}
    </div>
  );
}
