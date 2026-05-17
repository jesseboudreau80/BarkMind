# BarkMind — Behavioral Taxonomy

**Date:** 2026-05-17  
**Version:** 1.0 (seed)  
**Total terms:** 73 across 14 categories

---

## Design Principles

- **Extensible:** Taxonomy is data, not code. New terms are added via API/DB, not deploys.
- **Scientific language:** Labels use professional behavioral science terminology.
- **Severity hints:** 0=informational, 1=mild, 2=moderate, 3=elevated, 4=severe.
- **Signal types:** Each term has a `signal_type` for future signal-class filtering.
- **Hierarchy-ready:** `parent_id` FK exists for sub-categorization; all seed terms are flat.

---

## Signal Types

| Signal Type | Description |
|---|---|
| `neutral` | No behavioral communication |
| `play` | Play-soliciting or play-engagement signal |
| `appeasement` | Signal to reduce social pressure |
| `stress` | Indicator of psychological stress |
| `fear` | Active fear response |
| `arousal` | Physiological arousal, context-dependent |
| `threat` | Offensive or warning signal |
| `social` | Social communication signal |
| `avoidance` | Distance-increasing behavior |
| `resource` | Resource guarding or competition signal |
| `handler` | Handler action or response |
| `trigger` | Environmental factor initiating behavior |
| `conflict` | Ambivalent/conflicted state |
| `submission` | Social submission |

---

## Category Reference

### body_posture (8 terms)
Observable posture signals from full body position and musculature.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| posture_forward_lean | Forward Lean / Weight Forward | 2 | approach |
| posture_backward_lean | Backward Lean / Weight Shifted Away | 1 | avoidance |
| posture_crouch | Crouch / Appeasement Posture | 1 | appeasement |
| posture_freeze | Freeze / Stillness | 3 | threat |
| posture_bounce | Bouncy / Loose Movement | 0 | play |
| posture_lateral_roll | Lateral Roll / On Side or Back | 0 | submission |
| posture_stiff | Rigid / Stiff Body | 3 | threat |
| posture_piloerection | Piloerection / Raised Hackles | 2 | arousal |

### tail_position (5 terms)
Observable tail position and movement quality.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| tail_high_stiff | Tail High and Stiff / Flagging | 2 | arousal |
| tail_neutral_loose | Tail Neutral / Loose | 0 | neutral |
| tail_low_tucked | Tail Low / Tucked | 1 | fear |
| tail_loose_broad_wag | Loose Broad Wag | 0 | play |
| tail_fast_stiff_wag | Fast Stiff Wag (Arousal Wag) | 2 | arousal |

### ear_position (5 terms)
Ear carriage and orientation.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| ears_forward_erect | Ears Forward / Erect | 1 | alert |
| ears_neutral_relaxed | Ears Neutral / Relaxed | 0 | neutral |
| ears_pinned_flat | Ears Pinned Flat Back | 2 | fear |
| ears_rotated_back_soft | Ears Rotated Gently Back | 1 | appeasement |
| ears_asymmetric | Ears Asymmetric / Split | 1 | conflict |

### eye_contact (5 terms)
Eye expression and gaze direction.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| eye_hard_stare | Hard Stare / Sustained Eye Contact | 3 | threat |
| eye_soft_gaze | Soft Gaze / Relaxed Eye | 0 | neutral |
| eye_avoidance | Gaze Avoidance / Looking Away | 1 | appeasement |
| eye_whale_eye | Whale Eye / Sclera Showing | 2 | stress |
| eye_dilated_pupils | Dilated Pupils | 2 | arousal |

### mouth_tension (7 terms)
Lip, jaw, and muzzle expression.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| mouth_relaxed_open | Mouth Relaxed / Open | 0 | neutral |
| mouth_closed_tight | Mouth Closed Tight | 2 | stress |
| mouth_commissure_pulled | Commissure Pulled Back | 1 | appeasement |
| mouth_lip_lick | Lip Lick / Tongue Flick | 1 | stress |
| mouth_stress_yawn | Stress Yawn | 1 | stress |
| mouth_teeth_visible | Teeth Visible / Teeth Show | 3 | threat |
| mouth_snarl | Snarl / Lifted Lip with Tension | 4 | threat |

### stress_indicators (5 terms)
Non-specific stress behaviors.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| stress_panting | Stress Panting | 1 | stress |
| stress_shake_off | Shake Off | 1 | stress |
| stress_displacement | Displacement Behavior | 1 | stress |
| stress_drooling | Stress Drooling | 2 | stress |
| stress_trembling | Trembling / Shaking | 2 | fear |

### fear_indicators (4 terms)
Active fear responses.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| fear_freeze | Fear Freeze | 3 | fear |
| fear_flee_attempt | Flee / Escape Attempt | 2 | fear |
| fear_crouch_cower | Crouch / Cower | 2 | fear |
| fear_muzzle_punch | Muzzle Lick of Other Dog | 2 | appeasement |

### play_signals (4 terms)
Indicators of play intent and quality.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| play_bow | Play Bow | 0 | play |
| play_face | Play Face / Open Relaxed Mouth | 0 | play |
| play_self_handicap | Self-Handicapping | 0 | play |
| play_role_reversal | Role Reversal in Chase | 0 | play |

### arousal_escalation (4 terms)
Arousal state descriptors.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| arousal_low | Low Arousal / Relaxed | 0 | arousal |
| arousal_moderate | Moderate Arousal / Alert | 1 | arousal |
| arousal_high | High Arousal / Difficulty Recovering | 3 | arousal |
| arousal_threshold_break | Threshold Break / Over Threshold | 4 | arousal |

### social_engagement (5 terms)
Social approach and greeting quality.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| social_greeting | Mutual Sniff Greeting | 0 | social |
| social_parallel_movement | Parallel Movement | 0 | social |
| social_t_approach | T-Shaped Approach | 0 | social |
| social_direct_approach | Direct / Head-On Approach | 2 | social |
| social_mounting | Mounting Behavior | 2 | social |

### avoidance (4 terms)
Distance-increasing behaviors.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| avoidance_head_turn | Head Turn / Look Away | 1 | avoidance |
| avoidance_body_curve | Body Curve / Arc Approach | 0 | avoidance |
| avoidance_active_block | Space Blocking | 2 | avoidance |
| avoidance_move_away | Moving Away / Disengaging | 1 | avoidance |

### resource_guarding (4 terms)
Behaviors associated with resource competition.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| rg_body_stiffening | Body Stiffening Over Resource | 2 | resource |
| rg_resource_covering | Body Over Resource | 2 | resource |
| rg_low_growl | Low Growl at Resource | 3 | resource |
| rg_snap | Snap Near Resource | 4 | resource |

### handler_intervention (6 terms)
Handler actions and their outcomes.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| handler_verbal_cue | Handler Verbal Cue / Command | 0 | handler |
| handler_leash_guidance | Leash Guidance / Management | 1 | handler |
| handler_body_block | Handler Body Block | 1 | handler |
| handler_redirect_success | Redirect — Successful | 0 | handler |
| handler_redirect_failed | Redirect — Unsuccessful | 2 | handler |
| handler_removal | Dog Removed from Situation | 2 | handler |

### environmental_triggers (7 terms)
Environmental factors that precede or trigger behavioral responses.

| Slug | Label | Severity | Signal |
|---|---|---|---|
| trigger_new_dog | New Dog Introduction | 1 | trigger |
| trigger_new_person | New Person Presence | 1 | trigger |
| trigger_confinement | Confinement Stress | 1 | trigger |
| trigger_resource_present | High-Value Resource Present | 2 | trigger |
| trigger_auditory | Auditory Stimulus | 1 | trigger |
| trigger_handler_departure | Handler Departure / Separation | 1 | trigger |
| trigger_group_arousal | Group Arousal Contagion | 2 | trigger |

---

## Taxonomy Extension Protocol

To add new terms:
1. Choose a unique slug (snake_case, globally unique)
2. Choose the appropriate category (or create a new category)
3. Set severity_hint (0–4)
4. Set signal_type from the signal types table
5. POST to /taxonomy with admin credentials

No code changes are required. Taxonomy is pure data.

---

## Future: Taxonomy Hierarchy

When sub-categorization is needed:
1. Create parent term: `POST /taxonomy` with `slug: "tail_position"`, no parent_id
2. Create child terms: `POST /taxonomy` with `parent_id: <parent_uuid>`

The `parent_id` FK is already defined. No migration needed.
