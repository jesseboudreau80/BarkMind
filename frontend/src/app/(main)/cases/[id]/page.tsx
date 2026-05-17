"use client";

import { use, useState } from "react";
import useSWR from "swr";
import { cases as casesApi, comments as commentsApi, tags as tagsApi, timeline as timelineApi } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { formatRelativeTime, formatDate, formatSetting } from "@/lib/utils";
import { PageSpinner } from "@/components/ui/Spinner";
import Button from "@/components/ui/Button";
import StatusBadge from "@/components/cases/StatusBadge";
import { CaseTagBadge } from "@/components/cases/TagBadge";
import ExpertResolutionPanel from "@/components/cases/ExpertResolutionPanel";
import AnnotationList from "@/components/cases/AnnotationList";
import AnnotationForm from "@/components/forms/AnnotationForm";
import CommentThread from "@/components/cases/CommentThread";
import MediaGallery from "@/components/cases/MediaGallery";
import TimelineMarkers from "@/components/cases/TimelineMarkers";
import type { TagCategory } from "@/lib/types";
import {
  Calendar,
  Eye,
  MapPin,
  Tag,
  MessageSquare,
  PenLine,
  Zap,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

const CATEGORY_LABELS: Record<TagCategory, string> = {
  body_language: "Body Language",
  vocalization: "Vocalization",
  posture: "Posture",
  interaction: "Interaction",
  context: "Context",
};

export default function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { user } = useAuth();

  const {
    data: caseData,
    isLoading,
    error,
    mutate,
  } = useSWR(`case:${id}`, () => casesApi.get(id));

  const { data: allTags } = useSWR("tags", tagsApi.list);
  const { data: timelineData, mutate: mutateTimeline } = useSWR(
    `timeline:${id}`,
    () => timelineApi.list(id)
  );

  const [videoSeekTarget, setVideoSeekTarget] = useState<number | null>(null);
  const [tagsOpen, setTagsOpen] = useState(true);
  const [annotationsOpen, setAnnotationsOpen] = useState(true);
  const [tagSlug, setTagSlug] = useState("");
  const [tagConf, setTagConf] = useState<"observed" | "probable" | "possible">("observed");
  const [tagNote, setTagNote] = useState("");
  const [applyingTag, setApplyingTag] = useState(false);
  const [tagError, setTagError] = useState("");

  async function applyTag() {
    if (!tagSlug) return;
    setApplyingTag(true);
    setTagError("");
    try {
      await tagsApi.applyToCase(id, {
        tag_slug: tagSlug,
        confidence: tagConf,
        timestamp_note: tagNote || undefined,
      });
      setTagSlug("");
      setTagNote("");
      mutate();
    } catch (err: unknown) {
      setTagError(err instanceof Error ? err.message : "Failed to apply tag");
    } finally {
      setApplyingTag(false);
    }
  }

  if (isLoading) return <PageSpinner />;

  if (error || !caseData) {
    return (
      <div className="text-center py-16">
        <p className="text-zinc-400 font-medium">Case not found</p>
        <p className="text-sm text-zinc-600 mt-1">
          This case may have been archived or does not exist.
        </p>
      </div>
    );
  }

  const c = caseData;

  // Group tags by category
  const tagsByCategory = c.tags.reduce<Record<string, typeof c.tags>>((acc, ct) => {
    const cat = ct.tag.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(ct);
    return acc;
  }, {});

  return (
    <div className="max-w-5xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── LEFT COLUMN: main content ── */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {/* Case header */}
          <div className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <StatusBadge status={c.status} />
              <span className="text-xs text-zinc-600 font-mono shrink-0">
                #{c.id.split("-")[0]}
              </span>
            </div>
            <h1 className="text-2xl font-semibold text-zinc-100 leading-snug">
              {c.title}
            </h1>
            <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-500">
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(c.created_at)}
              </span>
              {c.setting && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  {formatSetting(c.setting)}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Eye className="h-3 w-3" />
                {c.view_count} views
              </span>
              <span>
                by{" "}
                <a
                  href={`/profile/${c.submitter.username}`}
                  className="text-zinc-400 hover:text-amber-400 transition-colors"
                >
                  {c.submitter.username}
                </a>
              </span>
            </div>
          </div>

          {/* Media */}
          <section>
            <MediaGallery media={c.media} seekTarget={videoSeekTarget} />
          </section>

          {/* Timeline markers (shown when video media exists) */}
          {(c.media.some((m) => m.media_type === "video") || (timelineData && timelineData.length > 0)) && (
            <section className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
              <TimelineMarkers
                caseId={id}
                mediaId={c.media.find((m) => m.media_type === "video")?.id}
                duration={c.media.find((m) => m.media_type === "video")?.duration_seconds}
                initialMarkers={timelineData ?? []}
                onMarkerClick={(ts) => setVideoSeekTarget(ts)}
                onMarkersChange={() => mutateTimeline()}
              />
            </section>
          )}

          {/* Expert resolution (prominent) */}
          {c.expert_resolution && (
            <ExpertResolutionPanel resolution={c.expert_resolution} />
          )}

          {/* AI summary */}
          {c.ai_summary && (
            <div className="rounded-xl border border-zinc-700/50 bg-zinc-900/50 p-4">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="h-4 w-4 text-amber-400" />
                <span className="text-sm font-medium text-zinc-300">AI-Assisted Summary</span>
                <span className="text-xs text-zinc-600">· Not a substitute for professional assessment</span>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line">
                {c.ai_summary}
              </p>
            </div>
          )}

          {/* Tags section */}
          <section>
            <button
              onClick={() => setTagsOpen((v) => !v)}
              className="w-full flex items-center gap-2 text-sm font-medium text-zinc-300 hover:text-zinc-100 transition-colors mb-3"
            >
              <Tag className="h-4 w-4 text-amber-400" />
              Behavioral Tags
              <span className="text-xs text-zinc-600 ml-1">({c.tags.length})</span>
              <span className="ml-auto">
                {tagsOpen ? (
                  <ChevronUp className="h-4 w-4 text-zinc-600" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-zinc-600" />
                )}
              </span>
            </button>

            {tagsOpen && (
              <div className="flex flex-col gap-3">
                {c.tags.length === 0 && (
                  <p className="text-sm text-zinc-600 italic">No behavioral tags applied yet.</p>
                )}
                {Object.entries(tagsByCategory).map(([cat, catTags]) => (
                  <div key={cat}>
                    <p className="text-xs text-zinc-600 uppercase tracking-wider mb-1.5">
                      {CATEGORY_LABELS[cat as TagCategory] ?? cat}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {catTags.map((ct) => (
                        <CaseTagBadge key={ct.id} caseTag={ct} />
                      ))}
                    </div>
                  </div>
                ))}

                {/* Apply tag form */}
                {user && allTags && (
                  <div className="mt-2 flex flex-wrap gap-2 items-end border-t border-zinc-800 pt-3">
                    <select
                      value={tagSlug}
                      onChange={(e) => setTagSlug(e.target.value)}
                      className="h-8 px-2 text-xs bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-300 focus:outline-none focus:border-amber-500"
                    >
                      <option value="">— Apply tag —</option>
                      {Object.entries(allTags.categories).map(([cat, catTags]) => (
                        <optgroup key={cat} label={CATEGORY_LABELS[cat as TagCategory] ?? cat}>
                          {catTags.map((t) => (
                            <option key={t.slug} value={t.slug}>{t.label}</option>
                          ))}
                        </optgroup>
                      ))}
                    </select>
                    <select
                      value={tagConf}
                      onChange={(e) => setTagConf(e.target.value as typeof tagConf)}
                      className="h-8 px-2 text-xs bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-300 focus:outline-none focus:border-amber-500"
                    >
                      <option value="observed">Observed</option>
                      <option value="probable">Probable</option>
                      <option value="possible">Possible</option>
                    </select>
                    <input
                      type="text"
                      value={tagNote}
                      onChange={(e) => setTagNote(e.target.value)}
                      placeholder="Timestamp note (optional)"
                      className="h-8 px-2 text-xs bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-300 focus:outline-none focus:border-amber-500 flex-1 min-w-[140px]"
                    />
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={applyTag}
                      isLoading={applyingTag}
                      disabled={!tagSlug}
                    >
                      Apply
                    </Button>
                    {tagError && <p className="text-xs text-red-400 w-full">{tagError}</p>}
                  </div>
                )}
              </div>
            )}
          </section>

          {/* Annotations */}
          <section>
            <button
              onClick={() => setAnnotationsOpen((v) => !v)}
              className="w-full flex items-center gap-2 text-sm font-medium text-zinc-300 hover:text-zinc-100 transition-colors mb-3"
            >
              <PenLine className="h-4 w-4 text-amber-400" />
              Annotations
              <span className="text-xs text-zinc-600 ml-1">({c.annotations.length})</span>
              <span className="ml-auto">
                {annotationsOpen ? (
                  <ChevronUp className="h-4 w-4 text-zinc-600" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-zinc-600" />
                )}
              </span>
            </button>
            {annotationsOpen && (
              <div className="flex flex-col gap-4">
                <AnnotationList annotations={c.annotations} />
                {user && (
                  <AnnotationForm caseId={id} onAdded={() => mutate()} />
                )}
              </div>
            )}
          </section>

          {/* Comments */}
          <section>
            <div className="flex items-center gap-2 text-sm font-medium text-zinc-300 mb-3">
              <MessageSquare className="h-4 w-4 text-amber-400" />
              Community Discussion
              <span className="text-xs text-zinc-600 ml-1">({c.comments_count})</span>
            </div>
            <CommentThread
              caseId={id}
              initialComments={[]}
            />
          </section>
        </div>

        {/* ── RIGHT COLUMN: case metadata ── */}
        <aside className="flex flex-col gap-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-3 text-sm">
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">
              Case Details
            </h3>
            <MetaRow label="Status">
              <StatusBadge status={c.status} />
            </MetaRow>
            {c.setting && (
              <MetaRow label="Setting">{formatSetting(c.setting)}</MetaRow>
            )}
            {c.subject_age_estimate && (
              <MetaRow label="Subject Age" className="capitalize">
                {c.subject_age_estimate}
              </MetaRow>
            )}
            {c.subject_breed_note && (
              <MetaRow label="Breed Note">{c.subject_breed_note}</MetaRow>
            )}
            {c.trigger_context && (
              <div>
                <p className="text-xs text-zinc-500 mb-1">Trigger Context</p>
                <p className="text-xs text-zinc-300 leading-relaxed">{c.trigger_context}</p>
              </div>
            )}
          </div>

          {c.description && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                Description
              </h3>
              <p className="text-sm text-zinc-300 leading-relaxed">{c.description}</p>
            </div>
          )}

          {/* Submitter */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
              Submitted By
            </h3>
            <a
              href={`/profile/${c.submitter.username}`}
              className="text-sm text-amber-400 hover:underline"
            >
              {c.submitter.username}
            </a>
            <p className="text-xs text-zinc-600 mt-1">{formatRelativeTime(c.created_at)}</p>
          </div>

          {/* Expert resolve button */}
          {user && (user.role === "expert" || user.role === "admin") && !c.expert_resolution && (
            <a
              href={`/expert/${id}`}
              className="flex items-center justify-center gap-2 h-9 px-4 text-sm font-medium rounded-lg bg-amber-400/10 border border-amber-500/50 text-amber-300 hover:bg-amber-400/20 transition-colors"
            >
              Resolve as Expert
            </a>
          )}
        </aside>
      </div>
    </div>
  );
}

function MetaRow({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="text-xs text-zinc-500 shrink-0">{label}</span>
      <span className={`text-xs text-zinc-300 text-right ${className ?? ""}`}>{children}</span>
    </div>
  );
}
