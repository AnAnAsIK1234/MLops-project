from __future__ import annotations

from sqlalchemy import select

from database.models import BalanceORM, UserORM
from .exceptions import NotFoundError


class UserService:
    def __init__(self, session):
        self.session = session

    def create_user(self, login: str, password_hash: str, role: str = "user") -> UserORM:
        existing = self.session.scalar(select(UserORM).where(UserORM.login == login))
        if existing is not None:
            raise ValueError("User already exists")

        user = UserORM(login=login, password_hash=password_hash, role=role)
        self.session.add(user)
        self.session.flush()

        user.balance = BalanceORM(user_id=user.id, credits=0)
        self.session.flush()
        return user

    def get_user(self, user_id: str) -> UserORM:
        user = self.session.get(UserORM, user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def get_by_login(self, login: str) -> UserORM | None:
        return self.session.scalar(select(UserORM).where(UserORM.login == login))