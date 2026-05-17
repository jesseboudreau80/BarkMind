import { cn } from "@/lib/utils";
import { Shield, CheckCircle2, Clock, Star } from "lucide-react";

interface ExpertProfile {
  username: string;
  display_name: string | null;
  display_title: string | null;
  organization: string | null;
  years_experience: number | null;
  certifications: { name: string; issuer?: string; year?: number }[];
  specializations: string[];
  verification_status: string;
  review_count: number;
  annotation_count: number;
  reputation_score: number;
}

const verificationConfig = {
  verified: {
    label: "Verified",
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    color: "text-emerald-400 bg-emerald-950/40 border-emerald-700",
  },
  pending: {
    label: "Pending",
    icon: <Clock className="h-3.5 w-3.5" />,
    color: "text-amber-400 bg-amber-950/40 border-amber-700",
  },
  unverified: {
    label: "Unverified",
    icon: <Shield className="h-3.5 w-3.5" />,
    color: "text-zinc-400 bg-zinc-800/40 border-zinc-700",
  },
};

export function VerificationBadge({
  status,
  compact = false,
}: {
  status: string;
  compact?: boolean;
}) {
  const cfg =
    verificationConfig[status as keyof typeof verificationConfig] ??
    verificationConfig.unverified;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 border rounded px-1.5 py-0.5 text-xs font-medium",
        cfg.color
      )}
    >
      {cfg.icon}
      {!compact && cfg.label}
    </span>
  );
}

export default function ExpertProfileCard({
  profile,
  compact = false,
}: {
  profile: ExpertProfile;
  compact?: boolean;
}) {
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className="w-7 h-7 rounded-full bg-amber-400/20 flex items-center justify-center text-amber-400 text-sm font-bold uppercase shrink-0">
          {profile.username[0]}
        </span>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-zinc-200">{profile.username}</span>
            <VerificationBadge status={profile.verification_status} compact />
          </div>
          {profile.display_title && (
            <span className="text-xs text-zinc-500">{profile.display_title}</span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-amber-400/20 flex items-center justify-center text-amber-400 text-lg font-bold uppercase shrink-0">
          {profile.username[0]}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-zinc-100">{profile.username}</span>
            <VerificationBadge status={profile.verification_status} />
          </div>
          {profile.display_title && (
            <p className="text-sm text-zinc-400 mt-0.5">{profile.display_title}</p>
          )}
          {profile.organization && (
            <p className="text-xs text-zinc-600">{profile.organization}</p>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        {[
          { value: profile.reputation_score, label: "Reputation" },
          { value: profile.review_count, label: "Reviews" },
          { value: profile.years_experience ?? "—", label: "Years Exp." },
        ].map((stat) => (
          <div
            key={stat.label}
            className="bg-zinc-800/50 rounded-lg py-2 flex flex-col gap-0.5"
          >
            <span className="text-sm font-semibold text-zinc-100">{stat.value}</span>
            <span className="text-xs text-zinc-600">{stat.label}</span>
          </div>
        ))}
      </div>

      {/* Certifications */}
      {profile.certifications.length > 0 && (
        <div>
          <p className="text-xs text-zinc-600 mb-1">Certifications</p>
          <div className="flex flex-wrap gap-1">
            {profile.certifications.map((cert, i) => (
              <span
                key={i}
                className="text-xs px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-300 font-mono"
              >
                {cert.name}
                {cert.year && <span className="text-zinc-600 ml-1">{cert.year}</span>}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Specializations */}
      {profile.specializations.length > 0 && (
        <div>
          <p className="text-xs text-zinc-600 mb-1">Specializations</p>
          <div className="flex flex-wrap gap-1">
            {profile.specializations.map((s) => (
              <span
                key={s}
                className="text-xs px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-300 capitalize"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
