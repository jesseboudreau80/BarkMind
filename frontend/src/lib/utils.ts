import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function formatSetting(setting: string | null): string {
  if (!setting) return "Unknown setting";
  const map: Record<string, string> = {
    daycare: "Dog Daycare",
    shelter: "Animal Shelter",
    home: "Home Environment",
    grooming: "Grooming Facility",
    vet: "Veterinary Clinic",
    other: "Other Setting",
  };
  return map[setting] ?? capitalize(setting);
}

export function formatBytes(bytes: number | null): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen - 3) + "...";
}

// Severity hint → label
export function severityLabel(hint: number): string {
  const labels = ["Info", "Mild", "Moderate", "Elevated", "Severe"];
  return labels[Math.min(hint, 4)] ?? "Info";
}

// Severity hint → Tailwind color class
export function severityColor(hint: number): string {
  const colors = [
    "text-zinc-400",
    "text-blue-400",
    "text-amber-400",
    "text-orange-400",
    "text-red-400",
  ];
  return colors[Math.min(hint, 4)] ?? "text-zinc-400";
}
