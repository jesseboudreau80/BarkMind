from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag

SEED_TAGS = [
    # body_language
    {"slug": "piloerection", "label": "Piloerection (Hackles)", "category": "body_language", "severity_hint": 2, "description": "Raised hackles along the spine or shoulders, indicating arousal or threat response."},
    {"slug": "tail_low", "label": "Tail Low / Tucked", "category": "body_language", "severity_hint": 1, "description": "Tail held low or tucked between legs, indicating fear or submission."},
    {"slug": "tail_stiff_high", "label": "Tail Stiff / High", "category": "body_language", "severity_hint": 2, "description": "Tail held stiffly upright, often with slow wagging, indicating alert or assertive state."},
    {"slug": "lip_lick", "label": "Lip Lick / Tongue Flick", "category": "body_language", "severity_hint": 1, "description": "Quick tongue flick to nose or lips, a calming/appeasement signal indicating mild stress."},
    {"slug": "yawn_stress", "label": "Stress Yawn", "category": "body_language", "severity_hint": 1, "description": "Exaggerated yawn in stressful context, used as a calming signal."},
    {"slug": "whale_eye", "label": "Whale Eye", "category": "body_language", "severity_hint": 2, "description": "White of the eye visible (sclera showing), indicating stress or threat anticipation."},
    {"slug": "avoidance", "label": "Avoidance / Turn Away", "category": "body_language", "severity_hint": 1, "description": "Dog turns head, body, or moves away from stimulus; a calming or appeasement signal."},
    {"slug": "freeze", "label": "Freeze / Stillness", "category": "body_language", "severity_hint": 3, "description": "Sudden cessation of movement; often precedes aggression."},
    {"slug": "crouch", "label": "Crouch / Appeasement", "category": "body_language", "severity_hint": 1, "description": "Low body posture, often with ears back and tail low, indicating submission or fear."},
    # vocalization
    {"slug": "low_growl", "label": "Low Growl", "category": "vocalization", "severity_hint": 3, "description": "Deep, low-pitched growl indicating warning or threat."},
    {"slug": "bark_repetitive", "label": "Repetitive Barking", "category": "vocalization", "severity_hint": 1, "description": "Continuous barking, context-dependent; may indicate alarm, excitement, or frustration."},
    {"slug": "whine", "label": "Whining", "category": "vocalization", "severity_hint": 1, "description": "High-pitched vocalizations indicating stress, frustration, or solicitation."},
    {"slug": "snap", "label": "Snap", "category": "vocalization", "severity_hint": 4, "description": "A quick bite motion, often without contact, as a final warning signal."},
    # posture
    {"slug": "forward_lean", "label": "Forward Lean / Assertive", "category": "posture", "severity_hint": 2, "description": "Weight shifted forward, direct stare; assertive or offensive posture."},
    {"slug": "lateral_recumbent", "label": "Lateral Recumbent (Submission)", "category": "posture", "severity_hint": 0, "description": "Dog rolls onto side or back, exposing belly; passive submission."},
    {"slug": "play_bow", "label": "Play Bow", "category": "posture", "severity_hint": 0, "description": "Front end lowered, rear end elevated; invitation to play."},
    # interaction
    {"slug": "mounting", "label": "Mounting Behavior", "category": "interaction", "severity_hint": 2, "description": "Mounting of another dog or human; may indicate arousal, stress, or social assertion."},
    {"slug": "resource_guard", "label": "Resource Guarding", "category": "interaction", "severity_hint": 3, "description": "Stiffening, growling, or snapping when approached near valued resource."},
    {"slug": "chase", "label": "Chase / Pursuit", "category": "interaction", "severity_hint": 2, "description": "Persistent pursuit of another dog or animal; may escalate to predatory behavior."},
    {"slug": "inhibited_bite", "label": "Inhibited Bite", "category": "interaction", "severity_hint": 3, "description": "Bite with reduced pressure resulting in no injury; warning bite."},
    # context
    {"slug": "new_environment", "label": "New Environment Exposure", "category": "context", "severity_hint": 0, "description": "Behavior occurring during first exposure to novel environment."},
    {"slug": "multi_dog", "label": "Multi-Dog Setting", "category": "context", "severity_hint": 0, "description": "Behavior occurring in presence of multiple dogs (daycare, park, etc.)."},
    {"slug": "handler_correction", "label": "Following Handler Correction", "category": "context", "severity_hint": 1, "description": "Behavior observed immediately following a handler correction or aversive."},
]


async def seed_tags(db: AsyncSession) -> int:
    existing = await db.execute(select(Tag.slug))
    existing_slugs = {row[0] for row in existing.fetchall()}

    added = 0
    for tag_data in SEED_TAGS:
        if tag_data["slug"] not in existing_slugs:
            db.add(Tag(**tag_data))
            added += 1

    if added:
        await db.commit()

    return added
