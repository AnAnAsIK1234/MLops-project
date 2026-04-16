from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from database.db import SessionLocal
from database.models import UserORM
from api.security import verify_password, unauthorized_exc

security = HTTPBasic()


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
    credentials: HTTPBasicCredentials = Depends(security),
    db=Depends(get_db),
) -> UserORM:
    user = db.query(UserORM).filter(UserORM.login == credentials.username).first()
    if user is None:
        raise unauthorized_exc()

    if not verify_password(credentials.password, user.password_hash):
        raise unauthorized_exc()

    if not user.is_active:
        raise unauthorized_exc()

    return user