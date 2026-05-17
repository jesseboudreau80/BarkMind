import type {
  AnnotationCreateBody,
  ApplyTagBody,
  CaseCreateBody,
  CaseDetail,
  CaseListResponse,
  Comment,
  CommentCreateBody,
  ExpertResolution,
  LoginResponse,
  RegisterResponse,
  ResolutionCreateBody,
  Tag,
  TagsGrouped,
  User,
  UserPublic,
} from "./types";

// All API calls go through Next.js rewrite proxy → backend
const API_BASE = "/api-backend";

class BarkMindApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public code: string
  ) {
    super(detail);
  }
}

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("barkmind_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new BarkMindApiError(
      res.status,
      data?.detail ?? "Request failed",
      data?.code ?? "unknown"
    );
  }

  return data as T;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const auth = {
  register: (body: {
    email: string;
    username: string;
    password: string;
    display_name?: string;
  }): Promise<RegisterResponse> =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  login: (email: string, password: string): Promise<LoginResponse> =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: (): Promise<User> => request("/auth/me"),

  logout: (): Promise<void> =>
    request("/auth/logout", { method: "POST" }),
};

// ─── Cases ────────────────────────────────────────────────────────────────────

export const cases = {
  list: (params?: {
    status?: string;
    tag?: string;
    setting?: string;
    search?: string;
    cursor?: string;
    limit?: number;
  }): Promise<CaseListResponse> => {
    const qs = params
      ? "?" + new URLSearchParams(
          Object.fromEntries(
            Object.entries(params).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
          )
        )
      : "";
    return request(`/cases${qs}`);
  },

  get: (id: string): Promise<CaseDetail> => request(`/cases/${id}`),

  create: (body: CaseCreateBody): Promise<{ id: string; status: string; created_at: string }> =>
    request("/cases", { method: "POST", body: JSON.stringify(body) }),

  patch: (id: string, body: Partial<CaseCreateBody>): Promise<CaseDetail> =>
    request(`/cases/${id}`, { method: "PATCH", body: JSON.stringify(body) }),

  archive: (id: string): Promise<void> =>
    request(`/cases/${id}`, { method: "DELETE" }),
};

// ─── Tags ─────────────────────────────────────────────────────────────────────

export const tags = {
  list: (): Promise<TagsGrouped> => request("/tags"),

  get: (slug: string): Promise<Tag> => request(`/tags/${slug}`),

  applyToCase: (caseId: string, body: ApplyTagBody): Promise<{ id: string; applied: boolean }> =>
    request(`/cases/${caseId}/tags`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  removeFromCase: (caseId: string, tagApplicationId: string): Promise<void> =>
    request(`/cases/${caseId}/tags/${tagApplicationId}`, { method: "DELETE" }),

  listOnCase: (caseId: string): Promise<import("./types").CaseTag[]> =>
    request(`/cases/${caseId}/tags`),
};

// ─── Annotations ──────────────────────────────────────────────────────────────

export const annotations = {
  list: (
    caseId: string,
    params?: {
      annotation_type?: string;
      confidence?: string;
      expert_only?: boolean;
      has_taxonomy?: boolean;
      timestamp_min?: number;
      timestamp_max?: number;
    }
  ) => {
    const qs = params
      ? "?" + new URLSearchParams(
          Object.fromEntries(
            Object.entries(params)
              .filter(([, v]) => v != null)
              .map(([k, v]) => [k, String(v)])
          )
        )
      : "";
    return request<import("./types").Annotation[]>(`/cases/${caseId}/annotations${qs}`);
  },

  create: (
    caseId: string,
    body: {
      annotation_type: string;
      body: string;
      media_id?: string;
      timestamp_start?: number;
      timestamp_end?: number;
      extra_data?: Record<string, unknown>;
      confidence_level?: string;
      taxonomy_term_slugs?: string[];
    }
  ) =>
    request<{ id: string; created: boolean }>(`/cases/${caseId}/annotations`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  edit: (
    caseId: string,
    annotationId: string,
    body: {
      body?: string;
      annotation_type?: string;
      confidence_level?: string;
      extra_data?: Record<string, unknown>;
      change_reason?: string;
    }
  ) =>
    request<import("./types").Annotation>(`/cases/${caseId}/annotations/${annotationId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  revisions: (caseId: string, annotationId: string) =>
    request<unknown[]>(`/cases/${caseId}/annotations/${annotationId}/revisions`),

  addTaxonomyRef: (caseId: string, annotationId: string, slug: string) =>
    request<{ attached: boolean; slug: string }>(
      `/cases/${caseId}/annotations/${annotationId}/taxonomy?slug=${encodeURIComponent(slug)}`,
      { method: "POST" }
    ),
};

// ─── Taxonomy ────────────────────────────────────────────────────────────────

export const taxonomy = {
  list: (activeOnly = true): Promise<import("./types").TaxonomyGrouped> =>
    request(`/taxonomy?active_only=${activeOnly}`),

  categories: (): Promise<{ categories: string[] }> =>
    request("/taxonomy/categories"),

  get: (slug: string): Promise<import("./types").TaxonomyTerm> =>
    request(`/taxonomy/${slug}`),
};

// ─── Timeline Markers ─────────────────────────────────────────────────────────

export const timeline = {
  list: (
    caseId: string,
    params?: { media_id?: string; marker_type?: string; expert_only?: boolean }
  ): Promise<import("./types").TimelineMarker[]> => {
    const qs = params
      ? "?" + new URLSearchParams(
          Object.fromEntries(
            Object.entries(params)
              .filter(([, v]) => v != null)
              .map(([k, v]) => [k, String(v)])
          )
        )
      : "";
    return request(`/cases/${caseId}/timeline${qs}`);
  },

  create: (
    caseId: string,
    body: {
      timestamp_seconds: number;
      label: string;
      marker_type?: string;
      media_id?: string;
      notes?: string;
    }
  ): Promise<import("./types").TimelineMarker> =>
    request(`/cases/${caseId}/timeline`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  delete: (caseId: string, markerId: string): Promise<void> =>
    request(`/cases/${caseId}/timeline/${markerId}`, { method: "DELETE" }),
};

// ─── Phase 5: Expert Profiles ─────────────────────────────────────────────────

export const expertProfiles = {
  list: (verifiedOnly = true): Promise<import("./types").ExpertProfile[]> =>
    request(`/experts?verified_only=${verifiedOnly}`),

  get: (username: string): Promise<import("./types").ExpertProfile> =>
    request(`/experts/${username}`),

  getMe: (): Promise<import("./types").ExpertProfile> => request("/experts/me"),

  createMe: (body: {
    display_title?: string;
    organization?: string;
    bio_professional?: string;
    years_experience?: number;
    certifications?: unknown[];
    specializations?: string[];
  }): Promise<import("./types").ExpertProfile> =>
    request("/experts/me", { method: "POST", body: JSON.stringify(body) }),

  updateMe: (body: object): Promise<import("./types").ExpertProfile> =>
    request("/experts/me", { method: "PATCH", body: JSON.stringify(body) }),

  verify: (userId: string, verificationStatus: string): Promise<import("./types").ExpertProfile> =>
    request(`/experts/${userId}/verify`, {
      method: "PATCH",
      body: JSON.stringify({ verification_status: verificationStatus }),
    }),
};

// ─── Phase 5: Reviews & Assignments ──────────────────────────────────────────

export const reviews = {
  getAssignments: (caseId: string): Promise<import("./types").ReviewAssignment[]> =>
    request(`/cases/${caseId}/assignments`),

  assign: (caseId: string, body: { assigned_to_username: string; review_type?: string; notes?: string }) =>
    request<import("./types").ReviewAssignment>(`/cases/${caseId}/assign`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  claim: (caseId: string): Promise<import("./types").ReviewAssignment> =>
    request(`/cases/${caseId}/claim`, { method: "POST" }),

  escalate: (caseId: string, reason?: string) =>
    request<{ case_id: string; status: string }>(`/cases/${caseId}/escalate?reason=${encodeURIComponent(reason ?? "")}`, {
      method: "POST",
    }),

  queue: (): Promise<{ assigned: import("./types").ReviewAssignment[]; claimable: unknown[] }> =>
    request("/reviews/queue"),

  lockEvidence: (caseId: string, body: { lock_state?: string; reason?: string }): Promise<import("./types").EvidenceLock> =>
    request(`/cases/${caseId}/lock`, { method: "POST", body: JSON.stringify(body) }),

  getLock: (caseId: string): Promise<import("./types").EvidenceLock> =>
    request(`/cases/${caseId}/lock`),

  updateStatus: (caseId: string, status: string, reason?: string) =>
    request<{ case_id: string; new_status: string }>(`/cases/${caseId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, reason }),
    }),
};

// ─── Phase 5: Consensus ───────────────────────────────────────────────────────

export const consensus = {
  get: (caseId: string): Promise<import("./types").ConsensusRecord> =>
    request(`/cases/${caseId}/consensus`),

  initiate: (caseId: string, notes?: string): Promise<import("./types").ConsensusRecord> =>
    request(`/cases/${caseId}/consensus`, {
      method: "POST",
      body: JSON.stringify({ notes }),
    }),

  submitOpinion: (
    caseId: string,
    body: { verdict: string; confidence_level?: string; summary?: string }
  ) =>
    request<{ opinion_id: string; verdict: string; current_tally: Record<string, number>; consensus_status: string; consensus_verdict: string | null }>(
      `/cases/${caseId}/consensus/opinion`,
      { method: "POST", body: JSON.stringify(body) }
    ),

  listOpinions: (caseId: string) => request<unknown>(`/cases/${caseId}/consensus/opinions`),
};

// ─── Phase 5: Audit ───────────────────────────────────────────────────────────

export const auditLog = {
  getCaseAudit: (caseId: string): Promise<import("./types").AuditEvent[]> =>
    request(`/audit/cases/${caseId}`),

  getGovernanceSummary: () => request<unknown>("/audit/governance/summary"),

  getReputationHistory: (username: string) => request<unknown>(`/audit/reputation/${username}`),
};

// ─── Comments ─────────────────────────────────────────────────────────────────

export const comments = {
  list: (caseId: string): Promise<Comment[]> =>
    request(`/cases/${caseId}/comments`),

  create: (caseId: string, body: CommentCreateBody): Promise<{ id: string; created: boolean }> =>
    request(`/cases/${caseId}/comments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

// ─── Media ────────────────────────────────────────────────────────────────────

export const media = {
  upload: async (
    caseId: string,
    file: File,
    onProgress?: (pct: number) => void
  ): Promise<{ id: string; url: string; media_type: string; processing_status: string }> => {
    const token = getStoredToken();
    const form = new FormData();
    form.append("file", file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE}/cases/${caseId}/media`);
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      xhr.onload = () => {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(data);
        } else {
          reject(new BarkMindApiError(xhr.status, data?.detail ?? "Upload failed", data?.code ?? "upload_error"));
        }
      };

      xhr.onerror = () => reject(new Error("Network error during upload"));
      xhr.send(form);
    });
  },

  list: (caseId: string) => request<unknown[]>(`/cases/${caseId}/media`),

  delete: (caseId: string, mediaId: string): Promise<void> =>
    request(`/cases/${caseId}/media/${mediaId}`, { method: "DELETE" }),
};

// ─── Resolutions ──────────────────────────────────────────────────────────────

export const resolutions = {
  get: (caseId: string): Promise<ExpertResolution> =>
    request(`/cases/${caseId}/resolution`),

  create: (caseId: string, body: ResolutionCreateBody): Promise<{ id: string; verdict: string }> =>
    request(`/cases/${caseId}/resolution`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  update: (caseId: string, body: ResolutionCreateBody): Promise<ExpertResolution> =>
    request(`/cases/${caseId}/resolution`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
};

// ─── Users ────────────────────────────────────────────────────────────────────

export const users = {
  me: (): Promise<User> => request("/users/me"),

  updateMe: (body: { display_name?: string; bio?: string }): Promise<User> =>
    request("/users/me", { method: "PATCH", body: JSON.stringify(body) }),

  profile: (username: string): Promise<UserPublic> =>
    request(`/users/${username}`),
};

export { BarkMindApiError };
