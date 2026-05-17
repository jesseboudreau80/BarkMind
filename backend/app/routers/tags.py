from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.deps import DB, CurrentUser
from app.models.tag import Tag
from app.schemas.tag import TagResponse, TagsGroupedResponse

router = APIRouter(prefix="/tags", tags=["tags"])

_CATEGORIES = ["body_language", "vocalization", "posture", "interaction", "context"]


@router.get("", response_model=TagsGroupedResponse)
async def list_tags(db: DB):
    result = await db.execute(select(Tag).order_by(Tag.category, Tag.label))
    tags = result.scalars().all()

    grouped: dict[str, list[TagResponse]] = {cat: [] for cat in _CATEGORIES}
    for tag in tags:
        cat = tag.category if tag.category in grouped else "context"
        grouped[cat].append(TagResponse.model_validate(tag))

    return TagsGroupedResponse(categories=grouped)


@router.get("/{slug}", response_model=TagResponse)
async def get_tag(slug: str, db: DB):
    result = await db.execute(select(Tag).where(Tag.slug == slug))
    tag = result.scalar_one_or_none()
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Tag not found", "code": "not_found"},
        )
    return TagResponse.model_validate(tag)


class TagCreate(BaseModel):
    slug: str
    label: str
    category: str
    description: str | None = None
    severity_hint: int = 0


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(body: TagCreate, db: DB, user: CurrentUser):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin role required", "code": "forbidden"},
        )
    existing = await db.execute(select(Tag).where(Tag.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Tag slug already exists", "code": "conflict"},
        )
    tag = Tag(**body.model_dump())
    db.add(tag)
    await db.flush()
    return TagResponse.model_validate(tag)
