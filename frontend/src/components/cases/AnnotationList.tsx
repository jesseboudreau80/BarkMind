"use client";

import { useState } from "react";
import type { Annotation } from "@/lib/types";
import AnnotationCard from "./AnnotationCard";
import { cn } from "@/lib/utils";

const FILTER_TYPES = [
  { value: "", label: "All types" },
  { value: "observation", label: "Observations" },
  { value: "interpretation", label: "Interpretations" },
  { value: "concern", label: "Concerns" },
  { value: "recommendation", label: "Recommendations" },
];

const FILTER_CONFIDENCE = [
  { value: "", label: "Any confidence" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

interface AnnotationListProps {
  annotations: Annotation[];
  onUpdate?: () => void;
}

export default function AnnotationList({ annotations, onUpdate }: AnnotationListProps) {
  const [filterType, setFilterType] = useState("");
  const [filterConfidence, setFilterConfidence] = useState("");
  const [expertOnly, setExpertOnly] = useState(false);
  const [hasTaxonomyOnly, setHasTaxonomyOnly] = useState(false);

  const filtered = annotations.filter((a) => {
    if (filterType && a.annotation_type !== filterType) return false;
    if (filterConfidence && a.confidence_level !== filterConfidence) return false;
    if (expertOnly && !a.is_expert) return false;
    if (hasTaxonomyOnly && a.taxonomy_refs.length === 0) return false;
    return true;
  });

  if (annotations.length === 0) {
    return (
      <div className="text-sm text-zinc-600 italic py-4">
        No annotations yet. Be the first to annotate this case.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Filter controls */}
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="h-7 px-2 text-xs bg-zinc-900 border border-zinc-800 rounded text-zinc-300 focus:outline-none focus:border-amber-500"
        >
          {FILTER_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
        <select
          value={filterConfidence}
          onChange={(e) => setFilterConfidence(e.target.value)}
          className="h-7 px-2 text-xs bg-zinc-900 border border-zinc-800 rounded text-zinc-300 focus:outline-none focus:border-amber-500"
        >
          {FILTER_CONFIDENCE.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
        <button
          onClick={() => setExpertOnly((v) => !v)}
          className={cn(
            "h-7 px-2 text-xs rounded border transition-colors",
            expertOnly
              ? "bg-amber-400/10 border-amber-500 text-amber-300"
              : "border-zinc-700 text-zinc-500 hover:border-zinc-600"
          )}
        >
          Expert only
        </button>
        <button
          onClick={() => setHasTaxonomyOnly((v) => !v)}
          className={cn(
            "h-7 px-2 text-xs rounded border transition-colors",
            hasTaxonomyOnly
              ? "bg-blue-400/10 border-blue-500 text-blue-300"
              : "border-zinc-700 text-zinc-500 hover:border-zinc-600"
          )}
        >
          Has taxonomy
        </button>
        {(filterType || filterConfidence || expertOnly || hasTaxonomyOnly) && (
          <button
            onClick={() => {
              setFilterType("");
              setFilterConfidence("");
              setExpertOnly(false);
              setHasTaxonomyOnly(false);
            }}
            className="text-xs text-zinc-600 hover:text-zinc-400"
          >
            Clear filters
          </button>
        )}
        <span className="text-xs text-zinc-700 ml-auto">
          {filtered.length}/{annotations.length}
        </span>
      </div>

      {/* Annotation cards */}
      {filtered.length === 0 ? (
        <p className="text-xs text-zinc-600 italic py-2">
          No annotations match these filters.
        </p>
      ) : (
        <div className="flex flex-col gap-2">
          {filtered.map((ann) => (
            <AnnotationCard key={ann.id} annotation={ann} onUpdate={onUpdate} />
          ))}
        </div>
      )}
    </div>
  );
}
