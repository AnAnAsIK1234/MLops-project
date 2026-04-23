from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.security import decode_access_token, unauthorized_exc
from database.db import SessionLocal
from database.models import UserORM

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db=Depends(get_db),
) -> UserORM:
    if credentials is None:
        raise unauthorized_exc()

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise unauthorized_exc()

    user = db.get(UserORM, user_id)
    if user is None or not user.is_active:
        raise unauthorized_exc()

    return user