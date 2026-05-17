import { Lock, Calendar } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface EvidenceLockBannerProps {
  lockedAt: string;
  lockedBy: string;
  lockState: string;
  reason: string | null;
}

export default function EvidenceLockBanner({
  lockedAt,
  lockedBy,
  lockState,
  reason,
}: EvidenceLockBannerProps) {
  return (
    <div className="rounded-xl border border-zinc-600/40 bg-zinc-800/30 p-4 flex items-start gap-3">
      <Lock className="h-4 w-4 text-zinc-400 mt-0.5 shrink-0" />
      <div className="flex flex-col gap-1 text-sm">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-zinc-200">Evidence Locked</span>
          <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded border border-zinc-700 font-mono">
            {lockState}
          </span>
        </div>
        <p className="text-xs text-zinc-500">
          Locked by{" "}
          <span className="text-zinc-400">{lockedBy}</span>
          {" on "}
          {formatDate(lockedAt)}
          {reason && (
            <>
              {" · "}
              <span className="italic">{reason}</span>
            </>
          )}
        </p>
        <p className="text-xs text-zinc-700">
          Annotations and media are frozen for dataset integrity.
        </p>
      </div>
    </div>
  );
}
