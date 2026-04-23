from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasicCredentials

from api.dependencies import get_db, security, get_current_user
from api.schemas.auth import RegisterRequest, LoginResponse, UserResponse
from api.security import hash_password, verify_password, unauthorized_exc
from database.models import UserORM
from database.services.user_service import UserService

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db=Depends(get_db)):
    service = UserService(db)
    user = service.create_user(
        login=payload.login,
        password_hash=hash_password(payload.password),
    )
    return UserResponse(
        id=user.id,
        login=user.login,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@auth_router.post("/login", response_model=LoginResponse)
def login(
    credentials: HTTPBasicCredentials = Depends(security),
    db=Depends(get_db),
):
    service = UserService(db)
    user = service.get_by_login(credentials.username)

    if user is None or not verify_password(credentials.password, user.password_hash):
        raise unauthorized_exc()

    return LoginResponse(
        message="Login successful",
        user_id=user.id,
        login=user.login,
        role=user.role,
    )


@auth_router.get("/me", response_model=UserResponse)
def me(current_user: UserORM = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        login=current_user.login,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )