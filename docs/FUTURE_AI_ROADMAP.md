# BarkMind — Future AI Roadmap

**Date:** 2026-05-17  
**Status:** Planning / Vision  
**Principle:** No fake AI. Ship real intelligence only when it adds genuine value.

---

## Phase 1 — AI Text Summary (MVP)

**Status:** In MVP scope  
**Stack:** Claude API via OpenClaw (`http://127.0.0.1:18789`)

### What It Does

Given a case (description, tags, annotations), generate a structured behavioral summary written in
the voice of a behavioral science practitioner.

### Prompt Strategy

Input context assembled from:
- Case description and trigger context
- Applied behavioral tags with confidence levels
- Expert and community annotations (observation, interpretation, concern, recommendation)
- Subject info (age estimate, setting)

Output format (structured, not free prose):
```
## Observed Behaviors
[Bulleted list from tags + observations]

## Behavioral Interpretation
[2-3 sentences: what the behaviors likely indicate]

## Level of Concern
[safe / mild / moderate / elevated — with reasoning]

## Recommended Actions
[If any — based on annotations tagged as "recommendation"]
```

### Implementation Details

- Model: `claude-sonnet-4-6` via OpenClaw
- Synchronous for MVP (no job queue)
- Prompt stored in `/prompts/behavioral_summary_v1.md`
- Version tracked in `cases.ai_summary_version`
- Requires expert or admin role to trigger

---

## Phase 2 — AI Tag Suggestions

**Status:** Post-MVP  
**Trigger:** Available after sufficient training data (500+ tagged cases)

### What It Does

Given a case description and any uploaded media, suggest behavioral tags that should be applied.

### Approach

- Text-only: analyze description + trigger context to suggest likely observable behaviors
- Return ranked list with confidence scores
- User applies or dismisses — AI does not auto-apply tags

### Value

Reduces tagging friction for community users unfamiliar with the full vocabulary.
Guides toward structured annotation even for novice submitters.

---

## Phase 3 — Multimodal Frame Analysis

**Status:** Post-MVP (requires Claude multimodal + ffmpeg pipeline)  
**Dependency:** Phase 3 media pipeline complete, frame extraction stable

### What It Does

Extract N frames from uploaded video. Send frames to Claude (multimodal) with a behavioral
analysis prompt. Return per-frame behavioral observations.

### Frame Extraction Strategy

```
1 frame per 2 seconds (or configurable density)
Max 50 frames per video (avoid cost explosion)
Frames stored in /media/cases/{case_id}/frames/
```

### Prompt Strategy

Each frame analyzed with context:
- What precedes this moment (case description, trigger)
- Subject age, setting
- Instruction: describe posture, body language signals visible in this frame

Aggregate frame analysis into:
- Timeline of observable behavioral states
- Peak moments of concern (ranked by severity)
- Overall escalation trajectory

### Cost Controls

- Frame analysis gated behind expert role (not open to all users)
- Per-case cost estimated before triggering
- Token usage logged to Aegis via OpenClaw audit

---

## Phase 4 — Behavioral Risk Scoring

**Status:** Future research phase  
**Dependency:** 1000+ expert-resolved cases as calibration data

### What It Does

Given a case, produce a multi-dimensional behavioral risk score:

| Dimension | Score | Description |
|---|---|---|
| Arousal Level | 0–10 | Physiological activation |
| Social Tension | 0–10 | Inter-dog or dog-human conflict potential |
| Escalation Trajectory | ↑↓→ | Increasing, decreasing, stable |
| Handler Risk | 0–10 | Probability of handler intervention needed |

### Approach

Initial approach: prompt-based scoring using Claude (fast to ship, revisable).
Later: fine-tuned classifier on expert-resolved case dataset.

### Validation

Scores are presented as AI estimates, not diagnoses.
Expert resolutions are used as ground truth for score calibration over time.

---

## Phase 5 — Predictive Escalation Detection (Research)

**Status:** Long-term research  
**Dependency:** Labeled video dataset + multimodal fine-tuning access

### What It Does

In a video clip, identify the moment when escalation risk transitions from low to high.
Flag the timestamp and explain the behavioral signals that indicate the transition.

### Use Cases

- Daycare staff reviewing incident footage
- Shelter staff assessing dog-dog compatibility
- Trainers reviewing session footage

### Data Requirements

- Expert-annotated video clips with escalation timestamps
- Minimum viable dataset: ~500 labeled clips
- Labels: start of escalation, peak escalation, de-escalation trigger

### Technical Approach

Phase 5a: Prompt-based with frame extraction — submit N frames with timestamps, ask Claude
to identify escalation onset. No fine-tuning required.

Phase 5b: Fine-tuned model on labeled dataset. Requires Anthropic fine-tuning access or
a vision model that supports behavioral fine-tuning.

---

## Phase 6 — Canine Behavioral Intelligence Dataset

**Status:** Long-term ecosystem goal

### What It Becomes

BarkMind's primary long-term value is the dataset:
- Expert-resolved behavior cases
- Annotated video with frame-level labels
- Structured behavioral tags with confidence ratings
- Expert verdicts as ground truth labels

This dataset is:
- Usable for behavioral model fine-tuning
- Exportable in JSONL format for training pipelines
- Citable as a structured behavioral research dataset
- Potentially publishable as an open dataset with contributor attribution

### Dataset Governance

- Users retain attribution for their annotations
- Dataset exports require admin approval
- Export format: JSONL with case metadata + annotation graph
- Media included only with submitter consent flag

---

## AI Guardrails (All Phases)

These rules apply to all AI features in BarkMind:

1. **AI output is never presented as veterinary diagnosis.** All AI summaries include a
   disclaimer: "AI-assisted analysis. Not a substitute for professional behavioral assessment."

2. **AI does not auto-apply tags.** All tags require human confirmation.

3. **AI summaries are version-tracked.** Prompt changes increment the version; old summaries
   remain stored with their version for auditability.

4. **All AI calls route through OpenClaw.** No direct Anthropic API calls from BarkMind.
   OpenClaw handles model routing, token logging, and rate limiting.

5. **AI features require elevated role.** AI summary generation requires expert or admin role
   for MVP. Future phases may open to verified users with rate limiting.

6. **No hallucination risk in structured scoring.** When AI produces scores, they are bounded
   (0–10 scales, enum verdicts). Free-text AI output is labeled as AI-generated.
