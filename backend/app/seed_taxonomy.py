"""
Behavioral taxonomy seed data for BarkMind.

This is the initial vocabulary. Taxonomy evolves as practitioners use the system.
Terms are organized by category. parent_id is NULL for all seed terms (flat seed).

Design principles:
- Slug: machine-readable, snake_case, globally unique
- Label: human-readable, professional behavioral science language
- Category: top-level grouping for UI display
- severity_hint in term_metadata: 0=informational, 1=mild, 2=moderate, 3=elevated, 4=severe
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taxonomy import TaxonomyTerm

TAXONOMY_SEED: list[dict] = [
    # ─── Body Posture ─────────────────────────────────────────────────────────
    {
        "slug": "posture_forward_lean",
        "label": "Forward Lean / Weight Forward",
        "category": "body_posture",
        "description": "Dog shifts weight toward stimulus; assertive or offensive intent.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 2, "signal_type": "approach"},
    },
    {
        "slug": "posture_backward_lean",
        "label": "Backward Lean / Weight Shifted Away",
        "category": "body_posture",
        "description": "Dog shifts weight away from stimulus; avoidance or uncertainty.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 1, "signal_type": "avoidance"},
    },
    {
        "slug": "posture_crouch",
        "label": "Crouch / Appeasement Posture",
        "category": "body_posture",
        "description": "Low body posture, often with ears back and tail low; submission or fear.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 1, "signal_type": "appeasement"},
    },
    {
        "slug": "posture_freeze",
        "label": "Freeze / Stillness",
        "category": "body_posture",
        "description": "Sudden cessation of movement; often precedes aggressive response.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 3, "signal_type": "threat"},
    },
    {
        "slug": "posture_bounce",
        "label": "Bouncy / Loose Movement",
        "category": "body_posture",
        "description": "Exaggerated bouncy gait; excited or play-seeking state.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 0, "signal_type": "play"},
    },
    {
        "slug": "posture_lateral_roll",
        "label": "Lateral Roll / On Side or Back",
        "category": "body_posture",
        "description": "Dog rolls onto side or back; passive submission or soliciting play.",
        "sort_order": 60,
        "term_metadata": {"severity_hint": 0, "signal_type": "submission"},
    },
    {
        "slug": "posture_stiff",
        "label": "Rigid / Stiff Body",
        "category": "body_posture",
        "description": "Tense, rigid musculature; high arousal or pre-aggression.",
        "sort_order": 70,
        "term_metadata": {"severity_hint": 3, "signal_type": "threat"},
    },
    {
        "slug": "posture_piloerection",
        "label": "Piloerection / Raised Hackles",
        "category": "body_posture",
        "description": "Hair raised along dorsal ridge (spine/shoulders); arousal signal.",
        "sort_order": 80,
        "term_metadata": {"severity_hint": 2, "signal_type": "arousal"},
    },

    # ─── Tail Position ────────────────────────────────────────────────────────
    {
        "slug": "tail_high_stiff",
        "label": "Tail High and Stiff / Flagging",
        "category": "tail_position",
        "description": "Tail held high and stiff, possibly with rapid stiff wagging; assertive arousal.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 2, "signal_type": "arousal"},
    },
    {
        "slug": "tail_neutral_loose",
        "label": "Tail Neutral / Loose",
        "category": "tail_position",
        "description": "Tail at natural position, not stiff; relaxed state.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 0, "signal_type": "neutral"},
    },
    {
        "slug": "tail_low_tucked",
        "label": "Tail Low / Tucked",
        "category": "tail_position",
        "description": "Tail held low or tucked between legs; fear or submission.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 1, "signal_type": "fear"},
    },
    {
        "slug": "tail_loose_broad_wag",
        "label": "Loose Broad Wag",
        "category": "tail_position",
        "description": "Wide, loose, whole-body wagging; friendly or playful.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 0, "signal_type": "play"},
    },
    {
        "slug": "tail_fast_stiff_wag",
        "label": "Fast Stiff Wag (Arousal Wag)",
        "category": "tail_position",
        "description": "Rapid wagging in tight arc; high arousal, context-dependent.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 2, "signal_type": "arousal"},
    },

    # ─── Ear Position ─────────────────────────────────────────────────────────
    {
        "slug": "ears_forward_erect",
        "label": "Ears Forward / Erect",
        "category": "ear_position",
        "description": "Ears pricked forward; alert, interested, or assertive.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 1, "signal_type": "alert"},
    },
    {
        "slug": "ears_neutral_relaxed",
        "label": "Ears Neutral / Relaxed",
        "category": "ear_position",
        "description": "Ears in natural resting position; calm state.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 0, "signal_type": "neutral"},
    },
    {
        "slug": "ears_pinned_flat",
        "label": "Ears Pinned Flat Back",
        "category": "ear_position",
        "description": "Ears pressed fully against skull; fear or extreme submission.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 2, "signal_type": "fear"},
    },
    {
        "slug": "ears_rotated_back_soft",
        "label": "Ears Rotated Gently Back",
        "category": "ear_position",
        "description": "Ears softly rotated back; mild appeasement or uncertainty.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 1, "signal_type": "appeasement"},
    },
    {
        "slug": "ears_asymmetric",
        "label": "Ears Asymmetric / Split",
        "category": "ear_position",
        "description": "One ear forward, one back; ambivalence or conflict state.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 1, "signal_type": "conflict"},
    },

    # ─── Eye Contact ──────────────────────────────────────────────────────────
    {
        "slug": "eye_hard_stare",
        "label": "Hard Stare / Sustained Eye Contact",
        "category": "eye_contact",
        "description": "Unblinking sustained stare; threat or challenge.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 3, "signal_type": "threat"},
    },
    {
        "slug": "eye_soft_gaze",
        "label": "Soft Gaze / Relaxed Eye",
        "category": "eye_contact",
        "description": "Soft, blinking, relaxed eye contact; comfortable or affiliative.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 0, "signal_type": "neutral"},
    },
    {
        "slug": "eye_avoidance",
        "label": "Gaze Avoidance / Looking Away",
        "category": "eye_contact",
        "description": "Actively avoiding eye contact; calming signal or submission.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 1, "signal_type": "appeasement"},
    },
    {
        "slug": "eye_whale_eye",
        "label": "Whale Eye / Sclera Showing",
        "category": "eye_contact",
        "description": "White of eye visible with head turned away; stress or threat anticipation.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 2, "signal_type": "stress"},
    },
    {
        "slug": "eye_dilated_pupils",
        "label": "Dilated Pupils",
        "category": "eye_contact",
        "description": "Pupils larger than context warrants; fear or high arousal.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 2, "signal_type": "arousal"},
    },

    # ─── Mouth / Muzzle Tension ───────────────────────────────────────────────
    {
        "slug": "mouth_relaxed_open",
        "label": "Mouth Relaxed / Open",
        "category": "mouth_tension",
        "description": "Loose lips, soft open mouth; relaxed state.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 0, "signal_type": "neutral"},
    },
    {
        "slug": "mouth_closed_tight",
        "label": "Mouth Closed Tight",
        "category": "mouth_tension",
        "description": "Lips pressed firmly together; tension or stress.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 2, "signal_type": "stress"},
    },
    {
        "slug": "mouth_commissure_pulled",
        "label": "Commissure Pulled Back",
        "category": "mouth_tension",
        "description": "Corners of mouth pulled toward ears; appeasement or fear.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 1, "signal_type": "appeasement"},
    },
    {
        "slug": "mouth_lip_lick",
        "label": "Lip Lick / Tongue Flick",
        "category": "mouth_tension",
        "description": "Quick tongue flick to nose or lips; calming signal, mild stress.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 1, "signal_type": "stress"},
    },
    {
        "slug": "mouth_stress_yawn",
        "label": "Stress Yawn",
        "category": "mouth_tension",
        "description": "Yawn in non-restful context; calming signal or stress indicator.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 1, "signal_type": "stress"},
    },
    {
        "slug": "mouth_teeth_visible",
        "label": "Teeth Visible / Teeth Show",
        "category": "mouth_tension",
        "description": "Lips lifted showing teeth; warning signal.",
        "sort_order": 60,
        "term_metadata": {"severity_hint": 3, "signal_type": "threat"},
    },
    {
        "slug": "mouth_snarl",
        "label": "Snarl / Lifted Lip with Tension",
        "category": "mouth_tension",
        "description": "Lip curled with muscular tension; active threat display.",
        "sort_order": 70,
        "term_metadata": {"severity_hint": 4, "signal_type": "threat"},
    },

    # ─── Stress Indicators ────────────────────────────────────────────────────
    {
        "slug": "stress_panting",
        "label": "Stress Panting",
        "category": "stress_indicators",
        "description": "Panting without exertion or heat; anxiety indicator.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 1, "signal_type": "stress"},
    },
    {
        "slug": "stress_shake_off",
        "label": "Shake Off",
        "category": "stress_indicators",
        "description": "Full-body shake after interaction; stress release signal.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 1, "signal_type": "stress"},
    },
    {
        "slug": "stress_displacement",
        "label": "Displacement Behavior",
        "category": "stress_indicators",
        "description": "Sniffing ground, scratching, etc. — irrelevant behavior during conflict.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 1, "signal_type": "stress"},
    },
    {
        "slug": "stress_drooling",
        "label": "Stress Drooling",
        "category": "stress_indicators",
        "description": "Excessive salivation without food present; anxiety.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 2, "signal_type": "stress"},
    },
    {
        "slug": "stress_trembling",
        "label": "Trembling / Shaking",
        "category": "stress_indicators",
        "description": "Visible body tremor; high fear or cold.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 2, "signal_type": "fear"},
    },

    # ─── Fear Indicators ──────────────────────────────────────────────────────
    {
        "slug": "fear_freeze",
        "label": "Fear Freeze",
        "category": "fear_indicators",
        "description": "Sudden stillness driven by fear; tonic immobility response.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 3, "signal_type": "fear"},
    },
    {
        "slug": "fear_flee_attempt",
        "label": "Flee / Escape Attempt",
        "category": "fear_indicators",
        "description": "Dog attempts to leave or pull away from stimulus.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 2, "signal_type": "fear"},
    },
    {
        "slug": "fear_crouch_cower",
        "label": "Crouch / Cower",
        "category": "fear_indicators",
        "description": "Body lowered with tucked tail; active fear response.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 2, "signal_type": "fear"},
    },
    {
        "slug": "fear_muzzle_punch",
        "label": "Muzzle Lick of Other Dog",
        "category": "fear_indicators",
        "description": "Dog licks muzzle of threatening dog; appeasement to avoid aggression.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 2, "signal_type": "appeasement"},
    },

    # ─── Play Signals ─────────────────────────────────────────────────────────
    {
        "slug": "play_bow",
        "label": "Play Bow",
        "category": "play_signals",
        "description": "Front end lowered, rear elevated; invitation to play.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 0, "signal_type": "play"},
    },
    {
        "slug": "play_face",
        "label": "Play Face / Open Relaxed Mouth",
        "category": "play_signals",
        "description": "Relaxed open mouth expression with soft eyes; play engagement.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 0, "signal_type": "play"},
    },
    {
        "slug": "play_self_handicap",
        "label": "Self-Handicapping",
        "category": "play_signals",
        "description": "Dog voluntarily yields, rolls, or slows to maintain play.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 0, "signal_type": "play"},
    },
    {
        "slug": "play_role_reversal",
        "label": "Role Reversal in Chase",
        "category": "play_signals",
        "description": "Chaser and chasee switch roles; key healthy play marker.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 0, "signal_type": "play"},
    },

    # ─── Arousal Escalation ───────────────────────────────────────────────────
    {
        "slug": "arousal_low",
        "label": "Low Arousal / Relaxed",
        "category": "arousal_escalation",
        "description": "Dog is calm and relaxed; baseline state.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 0, "signal_type": "arousal"},
    },
    {
        "slug": "arousal_moderate",
        "label": "Moderate Arousal / Alert",
        "category": "arousal_escalation",
        "description": "Dog is alert and engaged but still manageable.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 1, "signal_type": "arousal"},
    },
    {
        "slug": "arousal_high",
        "label": "High Arousal / Difficulty Recovering",
        "category": "arousal_escalation",
        "description": "Highly aroused state; dog has difficulty self-regulating.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 3, "signal_type": "arousal"},
    },
    {
        "slug": "arousal_threshold_break",
        "label": "Threshold Break / Over Threshold",
        "category": "arousal_escalation",
        "description": "Dog has exceeded their stimulus threshold; behavior changes.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 4, "signal_type": "arousal"},
    },

    # ─── Social Engagement ────────────────────────────────────────────────────
    {
        "slug": "social_greeting",
        "label": "Mutual Sniff Greeting",
        "category": "social_engagement",
        "description": "Reciprocal nose-to-nose or nose-to-rear greeting.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 0, "signal_type": "social"},
    },
    {
        "slug": "social_parallel_movement",
        "label": "Parallel Movement",
        "category": "social_engagement",
        "description": "Moving alongside without direct approach; appropriate social engagement.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 0, "signal_type": "social"},
    },
    {
        "slug": "social_t_approach",
        "label": "T-Shaped Approach",
        "category": "social_engagement",
        "description": "One dog approaches perpendicular to the other; appropriate first greeting.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 0, "signal_type": "social"},
    },
    {
        "slug": "social_direct_approach",
        "label": "Direct / Head-On Approach",
        "category": "social_engagement",
        "description": "Dog approaches directly face-to-face; pressure-generating.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 2, "signal_type": "social"},
    },
    {
        "slug": "social_mounting",
        "label": "Mounting Behavior",
        "category": "social_engagement",
        "description": "Mounting another dog; can indicate arousal, stress, or social assertion.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 2, "signal_type": "social"},
    },

    # ─── Avoidance Behaviors ──────────────────────────────────────────────────
    {
        "slug": "avoidance_head_turn",
        "label": "Head Turn / Look Away",
        "category": "avoidance",
        "description": "Dog turns head away from stimulus; calming signal.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 1, "signal_type": "avoidance"},
    },
    {
        "slug": "avoidance_body_curve",
        "label": "Body Curve / Arc Approach",
        "category": "avoidance",
        "description": "Dog curves body or approach path; calming signal.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 0, "signal_type": "avoidance"},
    },
    {
        "slug": "avoidance_active_block",
        "label": "Space Blocking",
        "category": "avoidance",
        "description": "Dog positions body to block access to resource or space.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 2, "signal_type": "avoidance"},
    },
    {
        "slug": "avoidance_move_away",
        "label": "Moving Away / Disengaging",
        "category": "avoidance",
        "description": "Dog moves away from stimulus to reduce pressure.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 1, "signal_type": "avoidance"},
    },

    # ─── Resource Guarding ────────────────────────────────────────────────────
    {
        "slug": "rg_body_stiffening",
        "label": "Body Stiffening Over Resource",
        "category": "resource_guarding",
        "description": "Dog stiffens when another approaches a valued resource.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 2, "signal_type": "resource"},
    },
    {
        "slug": "rg_resource_covering",
        "label": "Body Over Resource",
        "category": "resource_guarding",
        "description": "Dog positions body to cover or shield resource.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 2, "signal_type": "resource"},
    },
    {
        "slug": "rg_low_growl",
        "label": "Low Growl at Resource",
        "category": "resource_guarding",
        "description": "Dog growls when approached near valued resource.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 3, "signal_type": "resource"},
    },
    {
        "slug": "rg_snap",
        "label": "Snap Near Resource",
        "category": "resource_guarding",
        "description": "Quick bite motion (often without contact) when approached.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 4, "signal_type": "resource"},
    },

    # ─── Handler Intervention ─────────────────────────────────────────────────
    {
        "slug": "handler_verbal_cue",
        "label": "Handler Verbal Cue / Command",
        "category": "handler_intervention",
        "description": "Handler uses verbal cue to redirect or manage dog.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 0, "signal_type": "handler"},
    },
    {
        "slug": "handler_leash_guidance",
        "label": "Leash Guidance / Management",
        "category": "handler_intervention",
        "description": "Handler uses leash to guide or remove dog.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 1, "signal_type": "handler"},
    },
    {
        "slug": "handler_body_block",
        "label": "Handler Body Block",
        "category": "handler_intervention",
        "description": "Handler interposes their body to prevent escalation.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 1, "signal_type": "handler"},
    },
    {
        "slug": "handler_redirect_success",
        "label": "Redirect — Successful",
        "category": "handler_intervention",
        "description": "Handler successfully redirects dog's focus.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 0, "signal_type": "handler"},
    },
    {
        "slug": "handler_redirect_failed",
        "label": "Redirect — Unsuccessful",
        "category": "handler_intervention",
        "description": "Handler redirect attempt did not change dog's behavior.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 2, "signal_type": "handler"},
    },
    {
        "slug": "handler_removal",
        "label": "Dog Removed from Situation",
        "category": "handler_intervention",
        "description": "Handler physically removes dog from the trigger.",
        "sort_order": 60,
        "term_metadata": {"severity_hint": 2, "signal_type": "handler"},
    },

    # ─── Environmental Triggers ───────────────────────────────────────────────
    {
        "slug": "trigger_new_dog",
        "label": "New Dog Introduction",
        "category": "environmental_triggers",
        "description": "Behavior occurs during or after introduction to unfamiliar dog.",
        "sort_order": 10,
        "term_metadata": {"severity_hint": 1, "signal_type": "trigger"},
    },
    {
        "slug": "trigger_new_person",
        "label": "New Person Presence",
        "category": "environmental_triggers",
        "description": "Behavior triggered by unfamiliar human.",
        "sort_order": 20,
        "term_metadata": {"severity_hint": 1, "signal_type": "trigger"},
    },
    {
        "slug": "trigger_confinement",
        "label": "Confinement Stress",
        "category": "environmental_triggers",
        "description": "Behavior occurs in small or enclosed space.",
        "sort_order": 30,
        "term_metadata": {"severity_hint": 1, "signal_type": "trigger"},
    },
    {
        "slug": "trigger_resource_present",
        "label": "High-Value Resource Present",
        "category": "environmental_triggers",
        "description": "Food, toy, or resting spot in the environment.",
        "sort_order": 40,
        "term_metadata": {"severity_hint": 2, "signal_type": "trigger"},
    },
    {
        "slug": "trigger_auditory",
        "label": "Auditory Stimulus",
        "category": "environmental_triggers",
        "description": "Sudden or continuous sound triggers behavioral response.",
        "sort_order": 50,
        "term_metadata": {"severity_hint": 1, "signal_type": "trigger"},
    },
    {
        "slug": "trigger_handler_departure",
        "label": "Handler Departure / Separation",
        "category": "environmental_triggers",
        "description": "Handler moves away or leaves; separation-related trigger.",
        "sort_order": 60,
        "term_metadata": {"severity_hint": 1, "signal_type": "trigger"},
    },
    {
        "slug": "trigger_group_arousal",
        "label": "Group Arousal Contagion",
        "category": "environmental_triggers",
        "description": "Dog's arousal elevated by arousal of surrounding dogs.",
        "sort_order": 70,
        "term_metadata": {"severity_hint": 2, "signal_type": "trigger"},
    },
]


async def seed_taxonomy(db: AsyncSession) -> int:
    """Idempotently seed taxonomy terms. Returns count of terms added."""
    existing = await db.execute(select(TaxonomyTerm.slug))
    existing_slugs = {row[0] for row in existing.fetchall()}

    added = 0
    for term_data in TAXONOMY_SEED:
        if term_data["slug"] not in existing_slugs:
            db.add(TaxonomyTerm(**term_data))
            added += 1

    if added:
        await db.commit()

    return added
