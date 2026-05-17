"use client";

import { useState } from "react";
import useSWR from "swr";
import Button from "@/components/ui/Button";
import { Select, Textarea } from "@/components/ui/Input";
import { annotations as annotationsApi, taxonomy as taxonomyApi } from "@/lib/api";
import type { TaxonomyTerm } from "@/lib/types";
import { cn } from "@/lib/utils";

const TYPES = [
  { value: "observation", label: "Observation" },
  { value: "interpretation", label: "Interpretation" },
  { value: "concern", label: "Concern" },
  { value: "recommendation", label: "Recommendation" },
];

const CONFIDENCE_LEVELS = [
  { value: "", label: "Not specified" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const CATEGORY_LABELS: Record<string, string> = {
  body_posture: "Body Posture",
  tail_position: "Tail Position",
  ear_position: "Ear Position",
  eye_contact: "Eye Contact",
  mouth_tension: "Mouth Tension",
  stress_indicators: "Stress",
  fear_indicators: "Fear",
  play_signals: "Play Signals",
  arousal_escalation: "Arousal",
  social_engagement: "Social",
  avoidance: "Avoidance",
  resource_guarding: "Resource Guarding",
  handler_intervention: "Handler",
  environmental_triggers: "Triggers",
};

export default function AnnotationForm({
  caseId,
  onAdded,
}: {
  caseId: string;
  onAdded: () => void;
}) {
  const [type, setType] = useState("observation");
  const [body, setBody] = useState("");
  const [confidence, setConfidence] = useState("");
  const [tsStart, setTsStart] = useState("");
  const [tsEnd, setTsEnd] = useState("");
  const [selectedTaxonomy, setSelectedTaxonomy] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [taxonomyOpen, setTaxonomyOpen] = useState(false);

  const { data: taxonomyData } = useSWR(
    open ? "taxonomy" : null,
    () => taxonomyApi.list()
  );

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    setLoading(true);
    setError("");
    try {
      await annotationsApi.create(caseId, {
        annotation_type: type,
        body: body.trim(),
        timestamp_start: tsStart ? parseFloat(tsStart) : undefined,
        timestamp_end: tsEnd ? parseFloat(tsEnd) : undefined,
        confidence_level: confidence || undefined,
        taxonomy_term_slugs: selectedTaxonomy.length > 0 ? selectedTaxonomy : undefined,
      });
      setBody("");
      setTsStart("");
      setTsEnd("");
      setConfidence("");
      setSelectedTaxonomy([]);
      setOpen(false);
      onAdded();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add annotation");
    } finally {
      setLoading(false);
    }
  }

  function toggleTaxonomy(slug: string) {
    setSelectedTaxonomy((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]
    );
  }

  if (!open) {
    return (
      <Button variant="secondary" size="sm" onClick={() => setOpen(true)}>
        + Add Annotation
      </Button>
    );
  }

  return (
    <form
      onSubmit={submit}
      className="bg-zinc-900 border border-zinc-700 rounded-xl p-4 flex flex-col gap-3"
    >
      {/* Type + confidence row */}
      <div className="grid grid-cols-2 gap-2">
        <Select
          label="Type"
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          {TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </Select>
        <Select
          label="Confidence"
          value={confidence}
          onChange={(e) => setConfidence(e.target.value)}
        >
          {CONFIDENCE_LEVELS.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </Select>
      </div>

      {/* Timestamp range */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-zinc-500 shrink-0">Timestamp:</span>
        <input
          type="number"
          value={tsStart}
          onChange={(e) => setTsStart(e.target.value)}
          placeholder="Start (s)"
          step="0.1"
          className="w-24 h-8 px-2 text-xs bg-zinc-800 border border-zinc-700 rounded text-zinc-300 focus:outline-none focus:border-amber-500"
        />
        <span className="text-xs text-zinc-600">–</span>
        <input
          type="number"
          value={tsEnd}
          onChange={(e) => setTsEnd(e.target.value)}
          placeholder="End (s)"
          step="0.1"
          className="w-24 h-8 px-2 text-xs bg-zinc-800 border border-zinc-700 rounded text-zinc-300 focus:outline-none focus:border-amber-500"
        />
      </div>

      {/* Body */}
      <Textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Describe what you observed in precise behavioral terms..."
        className="min-h-[80px] text-sm"
        required
      />

      {/* Taxonomy picker (collapsible) */}
      <div>
        <button
          type="button"
          onClick={() => setTaxonomyOpen((v) => !v)}
          className="text-xs text-zinc-500 hover:text-amber-400 transition-colors flex items-center gap-1"
        >
          Behavioral taxonomy terms
          {selectedTaxonomy.length > 0 && (
            <span className="text-amber-400">({selectedTaxonomy.length} selected)</span>
          )}
        </button>

        {taxonomyOpen && taxonomyData && (
          <div className="mt-2 border border-zinc-800 rounded-lg p-3 bg-zinc-900/60 max-h-60 overflow-y-auto flex flex-col gap-3">
            {Object.entries(taxonomyData.categories).map(([cat, terms]) => (
              <div key={cat}>
                <p className="text-xs text-zinc-600 uppercase tracking-wider mb-1.5">
                  {CATEGORY_LABELS[cat] ?? cat}
                </p>
                <div className="flex flex-wrap gap-1">
                  {terms.map((term) => (
                    <button
                      key={term.slug}
                      type="button"
                      onClick={() => toggleTaxonomy(term.slug)}
                      className={cn(
                        "px-2 py-0.5 rounded text-xs border transition-colors font-mono",
                        selectedTaxonomy.includes(term.slug)
                          ? "bg-amber-400/10 border-amber-500 text-amber-300"
                          : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-600"
                      )}
                      title={term.description ?? ""}
                    >
                      {term.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <div className="flex gap-2">
        <Button type="submit" size="sm" isLoading={loading} disabled={!body.trim()}>
          Post Annotation
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => { setOpen(false); setTaxonomyOpen(false); }}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}
