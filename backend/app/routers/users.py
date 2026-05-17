from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.deps import CurrentUser, DB
from app.models.case import Case
from app.models.user import User
from app.schemas.user import UserMe, UserPublic, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMe)
async def get_me(user: CurrentUser):
    return UserMe.model_validate(user)


@router.patch("/me", response_model=UserMe)
async def update_me(body: UserUpdateRequest, db: DB, user: CurrentUser):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    return UserMe.model_validate(user)


@router.get("/{username}")
async def get_user_profile(username: str, db: DB):
    result = await db.execute(select(User).where(User.username == username, User.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "User not found", "code": "not_found"},
        )

    case_count = await db.scalar(
        select(func.count()).where(Case.submitter_id == user.id, Case.is_archived == False)
    )

    profile = UserPublic.model_validate(user)
    return {**profile.model_dump(), "case_count": case_count or 0}
