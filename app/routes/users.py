from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from api.schemas.auth import UserResponse
from database.models import UserORM

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/me", response_model=UserResponse)
def get_me(current_user: UserORM = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        login=current_user.login,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )