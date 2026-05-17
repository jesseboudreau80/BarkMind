"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { cn, formatBytes } from "@/lib/utils";
import type { CaseMedia } from "@/lib/types";
import { Play, Image as ImageIcon, ZoomIn, Clock, Maximize2, X } from "lucide-react";
import Spinner from "@/components/ui/Spinner";

// Prepend backend proxy path to a media URL
function proxyUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `/api-backend${url}`;
}

// Pick the best thumbnail URL from a media record
function getThumbnailUrl(m: CaseMedia, size: "sm" | "md" | "lg" = "md"): string | null {
  const thumbs = m.thumbnails;
  if (thumbs) {
    const sized = thumbs[size] ?? thumbs.md ?? thumbs.lg ?? thumbs.sm;
    if (sized) return proxyUrl(sized);
  }
  return proxyUrl(m.thumbnail_url);
}

// Format duration seconds as m:ss
function formatDuration(secs: number | null): string {
  if (!secs) return "";
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

interface LightboxProps {
  url: string;
  filename: string | null;
  onClose: () => void;
}

function Lightbox({ url, filename, onClose }: LightboxProps) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <button
        className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors"
        onClick={onClose}
        aria-label="Close"
      >
        <X className="h-6 w-6" />
      </button>
      <img
        src={url}
        alt={filename ?? "Full size image"}
        className="max-h-[90vh] max-w-[90vw] object-contain rounded-lg"
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  );
}

interface MediaItemProps {
  m: CaseMedia;
  onZoom: (url: string, filename: string | null) => void;
}

function ImageItem({ m, onZoom }: MediaItemProps) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const srcUrl = proxyUrl(m.url);
  // Use lg thumbnail for main view if available, fallback to original
  const displayUrl = getThumbnailUrl(m, "lg") ?? srcUrl;

  if (!displayUrl || error) {
    return (
      <div className="flex flex-col items-center gap-2 text-zinc-600">
        <ImageIcon className="h-10 w-10" />
        {m.processing_status === "pending" ? (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Spinner size="sm" />
            Generating thumbnails...
          </div>
        ) : (
          <span className="text-xs text-zinc-600">
            {error ? "Failed to load" : "Image unavailable"}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="relative group w-full h-full flex items-center justify-center">
      {!loaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Spinner size="md" />
        </div>
      )}
      <img
        src={displayUrl}
        alt={m.original_filename ?? "Case image"}
        className={cn(
          "max-h-full max-w-full object-contain transition-opacity duration-200 cursor-zoom-in",
          loaded ? "opacity-100" : "opacity-0"
        )}
        onLoad={() => setLoaded(true)}
        onError={() => { setError(true); setLoaded(true); }}
        onClick={() => srcUrl && onZoom(srcUrl, m.original_filename)}
      />
      {loaded && srcUrl && (
        <button
          onClick={() => onZoom(srcUrl, m.original_filename)}
          className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity"
          aria-label="View full size"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

function VideoItem({ m, seekTarget }: { m: CaseMedia; seekTarget?: number | null }) {
  const srcUrl = proxyUrl(m.url);
  const posterUrl = getThumbnailUrl(m, "lg");
  const videoRef = useRef<HTMLVideoElement>(null);

  // Seek to target when it changes
  useEffect(() => {
    if (seekTarget != null && videoRef.current) {
      videoRef.current.currentTime = seekTarget;
      videoRef.current.play().catch(() => {});
    }
  }, [seekTarget]);

  if (!srcUrl) {
    return (
      <div className="flex flex-col items-center gap-2 text-zinc-600">
        <Play className="h-10 w-10" />
        {m.processing_status === "pending" && (
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <Spinner size="sm" />
            Processing video...
          </div>
        )}
      </div>
    );
  }

  return (
    <video
      ref={videoRef}
      src={srcUrl}
      poster={posterUrl ?? undefined}
      controls
      playsInline
      preload="metadata"
      className="max-h-full max-w-full rounded"
    />
  );
}

export default function MediaGallery({
  media,
  seekTarget,
}: {
  media: CaseMedia[];
  seekTarget?: number | null;
}) {
  const [active, setActive] = useState(0);
  const [lightbox, setLightbox] = useState<{ url: string; filename: string | null } | null>(null);

  const openLightbox = useCallback((url: string, filename: string | null) => {
    setLightbox({ url, filename });
  }, []);

  if (media.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/30 flex items-center justify-center h-40 text-zinc-600">
        <div className="flex flex-col items-center gap-2">
          <ImageIcon className="h-7 w-7" />
          <span className="text-sm">No media attached</span>
        </div>
      </div>
    );
  }

  const current = media[active];

  return (
    <>
      {lightbox && (
        <Lightbox
          url={lightbox.url}
          filename={lightbox.filename}
          onClose={() => setLightbox(null)}
        />
      )}

      <div className="flex flex-col gap-3">
        {/* ── Main viewer ── */}
        <div className="rounded-xl overflow-hidden border border-zinc-800 bg-zinc-950 aspect-video flex items-center justify-center relative">
          {current.media_type === "image" ? (
            <ImageItem m={current} onZoom={openLightbox} />
          ) : (
            <VideoItem m={current} seekTarget={seekTarget} />
          )}

          {/* Processing badge */}
          {current.processing_status === "pending" && (
            <div className="absolute bottom-2 right-2 flex items-center gap-1.5 bg-zinc-900/80 border border-zinc-700 rounded-md px-2 py-1 text-xs text-zinc-400">
              <Spinner size="sm" />
              Processing
            </div>
          )}
          {current.processing_status === "failed" && (
            <div className="absolute bottom-2 right-2 bg-red-950/80 border border-red-800 rounded-md px-2 py-1 text-xs text-red-400">
              Processing failed
            </div>
          )}
        </div>

        {/* ── Thumbnail strip ── */}
        {media.length > 1 && (
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin">
            {media.map((m, i) => {
              const thumbUrl = getThumbnailUrl(m, "sm");
              const isVideo = m.media_type === "video";
              return (
                <button
                  key={m.id}
                  onClick={() => setActive(i)}
                  className={cn(
                    "shrink-0 w-16 h-16 rounded-lg border overflow-hidden transition-all relative",
                    i === active
                      ? "border-amber-400 ring-1 ring-amber-400/30"
                      : "border-zinc-700 hover:border-zinc-500 opacity-70 hover:opacity-100"
                  )}
                  aria-label={`View media ${i + 1}`}
                >
                  {thumbUrl ? (
                    <img
                      src={thumbUrl}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full bg-zinc-800 flex items-center justify-center text-zinc-600">
                      {isVideo ? <Play className="h-5 w-5" /> : <ImageIcon className="h-5 w-5" />}
                    </div>
                  )}
                  {isVideo && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="bg-black/50 rounded-full p-1">
                        <Play className="h-3 w-3 text-white fill-white" />
                      </div>
                    </div>
                  )}
                  {m.processing_status === "pending" && (
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                      <Spinner size="sm" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {/* ── Media metadata ── */}
        <div className="flex items-center gap-3 text-xs text-zinc-600 font-mono">
          {current.original_filename && (
            <span className="truncate max-w-[200px]">{current.original_filename}</span>
          )}
          {current.mime_type && <span>{current.mime_type}</span>}
          {current.size_bytes != null && <span>{formatBytes(current.size_bytes)}</span>}
          {current.width_px && current.height_px && (
            <span>{current.width_px}×{current.height_px}</span>
          )}
          {current.duration_seconds != null && (
            <span className="flex items-center gap-0.5">
              <Clock className="h-3 w-3" />
              {formatDuration(current.duration_seconds)}
            </span>
          )}
        </div>
      </div>
    </>
  );
}
