from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.case import Case
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentResponse

router = APIRouter(prefix="/cases", tags=["comments"])


@router.get("/{case_id}/comments")
async def list_comments(case_id: UUID, db: DB):
    result = await db.execute(
        select(Comment)
        .where(
            Comment.case_id == case_id,
            Comment.is_archived == False,
            Comment.parent_id == None,
        )
        .options(
            selectinload(Comment.author),
            selectinload(Comment.replies).selectinload(Comment.author),
        )
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()

    def _serialize(c: Comment) -> CommentResponse:
        return CommentResponse(
            id=c.id,
            case_id=c.case_id,
            author_username=c.author.username,
            body=c.body,
            parent_id=c.parent_id,
            is_archived=c.is_archived,
            replies=[_serialize(r) for r in c.replies if not r.is_archived],
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    return [_serialize(c) for c in comments]


@router.post("/{case_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(case_id: UUID, body: CommentCreate, db: DB, user: CurrentUser):
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    if case_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    if body.parent_id:
        parent_result = await db.execute(
            select(Comment).where(
                Comment.id == body.parent_id,
                Comment.case_id == case_id,
                Comment.is_archived == False,
            )
        )
        if parent_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=404,
                detail={"detail": "Parent comment not found", "code": "not_found"},
            )

    comment = Comment(
        case_id=case_id,
        author_id=user.id,
        body=body.body,
        parent_id=body.parent_id,
    )
    db.add(comment)
    await db.flush()
    return {"id": str(comment.id), "created": True}


@router.patch("/{case_id}/comments/{comment_id}")
async def edit_comment(case_id: UUID, comment_id: UUID, body: CommentCreate, db: DB, user: CurrentUser):
    result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.case_id == case_id,
            Comment.is_archived == False,
        )
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(status_code=404, detail={"detail": "Comment not found", "code": "not_found"})
    if comment.author_id != user.id:
        raise HTTPException(status_code=403, detail={"detail": "Not your comment", "code": "forbidden"})
    comment.body = body.body
    return {"id": str(comment.id), "updated": True}


@router.delete("/{case_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(case_id: UUID, comment_id: UUID, db: DB, user: CurrentUser):
    result = await db.execute(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.case_id == case_id,
            Comment.is_archived == False,
        )
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(status_code=404, detail={"detail": "Comment not found", "code": "not_found"})
    if comment.author_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail={"detail": "Not authorized", "code": "forbidden"})
    comment.is_archived = True
