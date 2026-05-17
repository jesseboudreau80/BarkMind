// Types mirroring the BarkMind backend API responses

export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string | null;
  bio: string | null;
  role: "user" | "expert" | "admin";
  reputation_score: number;
  created_at: string;
}

export interface UserBrief {
  username: string;
  reputation_score: number;
}

export interface UserPublic {
  id: string;
  username: string;
  display_name: string | null;
  bio: string | null;
  reputation_score: number;
  created_at: string;
  case_count: number;
}

export interface Tag {
  id: string;
  slug: string;
  label: string;
  category: TagCategory;
  description: string | null;
  severity_hint: number;
}

export type TagCategory =
  | "body_language"
  | "vocalization"
  | "posture"
  | "interaction"
  | "context";

export interface TagsGrouped {
  categories: Record<TagCategory, Tag[]>;
}

export interface CaseTag {
  id: string;
  tag: Tag;
  confidence: "observed" | "probable" | "possible" | null;
  timestamp_note: string | null;
  applied_by_username: string;
  created_at: string;
}

// Phase 4: Behavioral taxonomy
export interface TaxonomyTerm {
  id: string;
  slug: string;
  label: string;
  category: string;
  parent_id: string | null;
  description: string | null;
  sort_order: number;
  is_active: boolean;
  term_metadata: Record<string, unknown>;
  created_at: string;
}

export interface TaxonomyGrouped {
  categories: Record<string, TaxonomyTerm[]>;
  total: number;
}

export interface AnnotationTaxonomyRef {
  id: string;
  taxonomy_term_id: string;
  term: TaxonomyTerm;
  created_at: string;
}

export interface Annotation {
  id: string;
  annotation_type: "observation" | "interpretation" | "concern" | "recommendation";
  body: string;
  extra_data: Record<string, unknown>;
  timestamp_start: number | null;
  timestamp_end: number | null;
  is_expert: boolean;
  // Phase 4: enhanced fields
  confidence_level: "high" | "medium" | "low" | null;
  taxonomy_refs: AnnotationTaxonomyRef[];
  revision_count: number;
  author_username: string;
  created_at: string;
  updated_at: string;
}

// Phase 4: Timeline markers
export type MarkerType =
  | "event"
  | "escalation"
  | "de_escalation"
  | "handler_intervention"
  | "trigger"
  | "resolution"
  | "calming_signal"
  | "threshold_break"
  | "play_initiation"
  | "resource_guard";

export interface TimelineMarker {
  id: string;
  case_id: string;
  media_id: string | null;
  author_username: string;
  timestamp_seconds: number;
  label: string;
  marker_type: MarkerType;
  notes: string | null;
  is_expert: boolean;
  created_at: string;
  updated_at: string;
}

export interface ThumbnailSet {
  sm: string | null;
  md: string | null;
  lg: string | null;
}

export interface CaseMedia {
  id: string;
  case_id: string;
  media_type: "image" | "video";
  original_filename: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  // Phase 3: dimensions and duration
  width_px: number | null;
  height_px: number | null;
  duration_seconds: number | null;
  processing_status: "pending" | "ready" | "failed";
  thumbnail_url: string | null;
  thumbnails: ThumbnailSet | null;
  url: string | null;
  created_at: string;
}

export interface ExpertResolution {
  id: string;
  verdict: Verdict;
  summary: string;
  recommendations: string | null;
  confidence_level: "high" | "medium" | "low" | null;
  expert_username: string;
  created_at: string;
  updated_at: string;
}

export type Verdict =
  | "safe"
  | "concern"
  | "escalation_risk"
  | "requires_intervention";

// Phase 5: extended case states
export type CaseStatus =
  | "intake"
  | "open"
  | "under_review"
  | "expert_review"
  | "consensus_pending"
  | "escalated"
  | "resolved"
  | "locked"
  | "archived";

export type CaseSetting =
  | "daycare"
  | "shelter"
  | "home"
  | "grooming"
  | "vet"
  | "other";

export interface CaseListItem {
  id: string;
  title: string;
  status: CaseStatus;
  setting: CaseSetting | null;
  subject_age_estimate: string | null;
  submitter: UserBrief;
  view_count: number;
  created_at: string;
}

export interface CaseListResponse {
  items: CaseListItem[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface CaseDetail {
  id: string;
  title: string;
  description: string | null;
  status: CaseStatus;
  setting: CaseSetting | null;
  subject_age_estimate: string | null;
  subject_breed_note: string | null;
  trigger_context: string | null;
  species_context: string;
  submitter: UserBrief;
  tags: CaseTag[];
  annotations: Annotation[];
  media: CaseMedia[];
  comments_count: number;
  expert_resolution: ExpertResolution | null;
  ai_summary: string | null;
  view_count: number;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  case_id: string;
  author_username: string;
  body: string;
  parent_id: string | null;
  is_archived: boolean;
  replies: Comment[];
  created_at: string;
  updated_at: string;
}

// Auth
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: { id: string; username: string; role: string };
}

export interface RegisterResponse {
  user_id: string;
  username: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    username: string,
    password: string,
    displayName?: string
  ) => Promise<void>;
  logout: () => void;
}

// Request bodies
export interface CaseCreateBody {
  title: string;
  description?: string;
  setting?: CaseSetting;
  subject_age_estimate?: string;
  subject_breed_note?: string;
  trigger_context?: string;
}

export interface ApplyTagBody {
  tag_slug: string;
  confidence?: "observed" | "probable" | "possible";
  timestamp_note?: string;
}

export interface AnnotationCreateBody {
  annotation_type: "observation" | "interpretation" | "concern" | "recommendation";
  body: string;
  media_id?: string;
  timestamp_start?: number;
  timestamp_end?: number;
  extra_data?: Record<string, unknown>;
}

export interface CommentCreateBody {
  body: string;
  parent_id?: string;
}

export interface ResolutionCreateBody {
  verdict: Verdict;
  summary: string;
  recommendations?: string;
  confidence_level?: "high" | "medium" | "low";
}

export interface ApiError {
  detail: string;
  code: string;
}

// Phase 5: Trust infrastructure types

export interface ExpertProfile {
  id: string;
  user_id: string;
  username: string;
  display_name: string | null;
  display_title: string | null;
  organization: string | null;
  bio_professional: string | null;
  years_experience: number | null;
  certifications: { name: string; issuer?: string; year?: number; expiry_year?: number }[];
  specializations: string[];
  verification_status: "verified" | "pending" | "unverified";
  verified_at: string | null;
  review_count: number;
  annotation_count: number;
  consensus_agreement_count: number;
  reputation_score: number;
  created_at: string;
}

export interface ReviewAssignment {
  id: string;
  case_id: string;
  reviewer_username: string;
  assigner_username: string;
  status: "pending" | "claimed" | "in_review" | "complete" | "transferred" | "declined";
  review_type: "primary" | "secondary" | "escalation";
  notes: string | null;
  claimed_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ExpertOpinion {
  id: string;
  expert_username: string;
  verdict: Verdict;
  confidence_level: string | null;
  summary: string | null;
  created_at: string;
}

export interface ConsensusRecord {
  id: string;
  case_id: string;
  status: "open" | "reached" | "disputed" | "escalated";
  initiated_by_username: string;
  verdict_tally: Record<string, number>;
  consensus_verdict: Verdict | null;
  consensus_confidence: string | null;
  notes: string | null;
  opinion_count: number;
  opinions: ExpertOpinion[];
  created_at: string;
  updated_at: string;
}

export interface EvidenceLock {
  id: string;
  case_id: string;
  locked_by_username: string;
  locked_at: string;
  lock_state: "media" | "full";
  reason: string | null;
  snapshot: Record<string, unknown>;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  actor: string | null;
  target_type: string;
  target_id: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}
