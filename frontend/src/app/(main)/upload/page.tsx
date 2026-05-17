"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { cases as casesApi, media as mediaApi, tags as tagsApi } from "@/lib/api";
import { Input, Textarea, Select } from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { CaseTagBadge } from "@/components/cases/TagBadge";
import useSWR from "swr";
import type { TagCategory, ApplyTagBody } from "@/lib/types";
import { Upload, X, CheckCircle, FileImage, FileVideo } from "lucide-react";
import { cn, formatBytes } from "@/lib/utils";

const CATEGORY_LABELS: Record<TagCategory, string> = {
  body_language: "Body Language",
  vocalization: "Vocalization",
  posture: "Posture",
  interaction: "Interaction",
  context: "Context",
};

type Step = "context" | "media" | "tags" | "review";
const STEPS: Step[] = ["context", "media", "tags", "review"];
const STEP_LABELS: Record<Step, string> = {
  context: "1. Context",
  media: "2. Media",
  tags: "3. Tags",
  review: "4. Submit",
};

export default function UploadPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState<Step>("context");

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [setting, setSetting] = useState("");
  const [ageEstimate, setAgeEstimate] = useState("");
  const [breedNote, setBreedNote] = useState("");
  const [triggerContext, setTriggerContext] = useState("");

  // Media state
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Tags state
  const [selectedTags, setSelectedTags] = useState<ApplyTagBody[]>([]);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const { data: allTags } = useSWR("tags", tagsApi.list);

  if (!user) {
    return (
      <div className="text-center py-16">
        <p className="text-zinc-400 font-medium mb-3">Sign in to submit a case</p>
        <Button onClick={() => router.push("/login?return=/upload")}>Sign in</Button>
      </div>
    );
  }

  function addFiles(newFiles: FileList | null) {
    if (!newFiles) return;
    const accepted = Array.from(newFiles).filter(
      (f) =>
        ["image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime"].includes(
          f.type
        )
    );
    setFiles((prev) => [...prev, ...accepted]);
  }

  function removeFile(i: number) {
    setFiles((prev) => prev.filter((_, idx) => idx !== i));
  }

  function toggleTag(slug: string, label: string) {
    setSelectedTags((prev) => {
      const exists = prev.find((t) => t.tag_slug === slug);
      if (exists) return prev.filter((t) => t.tag_slug !== slug);
      return [...prev, { tag_slug: slug, confidence: "observed" }];
    });
  }

  async function handleSubmit() {
    if (!title.trim()) return;
    setSubmitting(true);
    setSubmitError("");

    try {
      // 1. Create case
      const created = await casesApi.create({
        title: title.trim(),
        description: description.trim() || undefined,
        setting: setting as "daycare" | "shelter" | "home" | "grooming" | "vet" | "other" | undefined,
        subject_age_estimate: ageEstimate || undefined,
        subject_breed_note: breedNote.trim() || undefined,
        trigger_context: triggerContext.trim() || undefined,
      });

      const caseId = created.id;

      // 2. Upload media
      for (const file of files) {
        await mediaApi.upload(caseId, file, (pct) => {
          setUploadProgress((prev) => ({ ...prev, [file.name]: pct }));
        });
      }

      // 3. Apply tags
      for (const tag of selectedTags) {
        await tagsApi.applyToCase(caseId, tag).catch(() => {});
      }

      router.push(`/cases/${caseId}`);
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  const stepIdx = STEPS.indexOf(step);

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-zinc-100">Submit a Behavior Case</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Document a canine behavioral incident for community review and analysis
        </p>
      </div>

      {/* Step progress */}
      <div className="flex items-center gap-1">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-1 flex-1">
            <button
              onClick={() => i < stepIdx && setStep(s)}
              disabled={i > stepIdx}
              className={cn(
                "flex-1 h-1.5 rounded-full transition-colors",
                i <= stepIdx ? "bg-amber-400" : "bg-zinc-800"
              )}
            />
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs text-zinc-500">
        {STEPS.map((s) => (
          <span key={s} className={step === s ? "text-amber-400" : ""}>
            {STEP_LABELS[s]}
          </span>
        ))}
      </div>

      {/* Step content */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4">
        {step === "context" && (
          <>
            <Input
              label="Case Title *"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Brief description of the behavioral incident"
              required
            />
            <Select
              label="Setting"
              value={setting}
              onChange={(e) => setSetting(e.target.value)}
            >
              <option value="">Select setting...</option>
              <option value="daycare">Dog Daycare</option>
              <option value="shelter">Animal Shelter</option>
              <option value="home">Home Environment</option>
              <option value="grooming">Grooming Facility</option>
              <option value="vet">Veterinary Clinic</option>
              <option value="other">Other</option>
            </Select>
            <div className="grid grid-cols-2 gap-3">
              <Select
                label="Subject Age"
                value={ageEstimate}
                onChange={(e) => setAgeEstimate(e.target.value)}
              >
                <option value="">Unknown</option>
                <option value="puppy">Puppy (&lt; 1yr)</option>
                <option value="adult">Adult (1–7yr)</option>
                <option value="senior">Senior (7yr+)</option>
              </Select>
              <Input
                label="Breed Note (optional)"
                value={breedNote}
                onChange={(e) => setBreedNote(e.target.value)}
                placeholder="Breed, mix, approx age"
              />
            </div>
            <Textarea
              label="Trigger Context"
              value={triggerContext}
              onChange={(e) => setTriggerContext(e.target.value)}
              placeholder="What preceded or triggered the behavior?"
              className="min-h-[80px]"
            />
            <Textarea
              label="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed description of what occurred"
              className="min-h-[80px]"
            />
          </>
        )}

        {step === "media" && (
          <div className="flex flex-col gap-4">
            <div
              onDrop={(e) => {
                e.preventDefault();
                addFiles(e.dataTransfer.files);
              }}
              onDragOver={(e) => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-zinc-700 hover:border-zinc-500 rounded-xl p-8 flex flex-col items-center gap-3 cursor-pointer transition-colors"
            >
              <Upload className="h-8 w-8 text-zinc-500" />
              <div className="text-center">
                <p className="text-sm text-zinc-300">Drop files here or click to browse</p>
                <p className="text-xs text-zinc-600 mt-1">
                  JPEG, PNG, WebP (20 MB) · MP4, MOV (500 MB)
                </p>
              </div>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime"
              multiple
              className="hidden"
              onChange={(e) => addFiles(e.target.files)}
            />

            {files.length > 0 && (
              <div className="flex flex-col gap-2">
                {files.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 bg-zinc-800/60 border border-zinc-700 rounded-lg px-3 py-2"
                  >
                    {f.type.startsWith("video/") ? (
                      <FileVideo className="h-4 w-4 text-zinc-400 shrink-0" />
                    ) : (
                      <FileImage className="h-4 w-4 text-zinc-400 shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-zinc-300 truncate">{f.name}</p>
                      <p className="text-xs text-zinc-600">{formatBytes(f.size)}</p>
                    </div>
                    {uploadProgress[f.name] != null && uploadProgress[f.name] < 100 && (
                      <div className="w-16 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-amber-400 transition-all"
                          style={{ width: `${uploadProgress[f.name]}%` }}
                        />
                      </div>
                    )}
                    {uploadProgress[f.name] === 100 && (
                      <CheckCircle className="h-4 w-4 text-emerald-400" />
                    )}
                    <button
                      onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                      className="text-zinc-600 hover:text-red-400 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            {files.length === 0 && (
              <p className="text-xs text-zinc-600 italic text-center">
                Media is optional. You can add it later.
              </p>
            )}
          </div>
        )}

        {step === "tags" && allTags && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-zinc-400">
              Select behavioral signals you observed. You can add more after submission.
            </p>
            {Object.entries(allTags.categories).map(([cat, catTags]) => (
              <div key={cat}>
                <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
                  {CATEGORY_LABELS[cat as TagCategory] ?? cat}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {catTags.map((tag) => {
                    const selected = selectedTags.some((t) => t.tag_slug === tag.slug);
                    return (
                      <button
                        key={tag.slug}
                        onClick={() => toggleTag(tag.slug, tag.label)}
                        className={cn(
                          "px-2.5 py-1 rounded text-xs font-mono border transition-colors",
                          selected
                            ? "bg-amber-400/10 border-amber-500 text-amber-300"
                            : "bg-zinc-800 border-zinc-700 text-zinc-400 hover:border-zinc-500"
                        )}
                        title={tag.description ?? ""}
                      >
                        {tag.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
            {selectedTags.length > 0 && (
              <div className="border-t border-zinc-800 pt-3">
                <p className="text-xs text-zinc-500 mb-2">
                  Selected ({selectedTags.length}):
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {selectedTags.map((t) => {
                    const tag = Object.values(allTags.categories)
                      .flat()
                      .find((tg) => tg.slug === t.tag_slug);
                    return tag ? (
                      <span
                        key={t.tag_slug}
                        className="px-2 py-0.5 rounded text-xs bg-amber-400/10 border border-amber-500/50 text-amber-300 font-mono"
                      >
                        {tag.label}
                      </span>
                    ) : null;
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {step === "review" && (
          <div className="flex flex-col gap-4 text-sm">
            <h3 className="font-medium text-zinc-200">Review your submission</h3>
            <div className="bg-zinc-800/60 border border-zinc-700 rounded-lg p-4 flex flex-col gap-2">
              <p className="font-medium text-zinc-100">{title}</p>
              {setting && <p className="text-zinc-400 capitalize">{setting}</p>}
              {description && <p className="text-zinc-500 text-xs line-clamp-3">{description}</p>}
            </div>
            <div className="flex gap-4 text-xs text-zinc-500">
              <span>{files.length} file{files.length !== 1 ? "s" : ""} attached</span>
              <span>{selectedTags.length} tag{selectedTags.length !== 1 ? "s" : ""} selected</span>
            </div>
            {submitError && (
              <div className="text-sm text-red-400 bg-red-950/30 border border-red-900 rounded-lg px-3 py-2">
                {submitError}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="secondary"
          onClick={() => setStep(STEPS[stepIdx - 1])}
          disabled={stepIdx === 0}
        >
          Back
        </Button>

        {step === "review" ? (
          <Button onClick={handleSubmit} isLoading={submitting} disabled={!title.trim()}>
            Submit Case
          </Button>
        ) : (
          <Button
            onClick={() => setStep(STEPS[stepIdx + 1])}
            disabled={step === "context" && !title.trim()}
          >
            Continue
          </Button>
        )}
      </div>
    </div>
  );
}
