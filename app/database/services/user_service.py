from __future__ import annotations

import json
from datetime import datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database.models import (
    BalanceORM,
    BalanceTransactionORM,
    JobStatus,
    MLModelORM,
    ModelSource,
    PredictionHistoryRecordORM,
    PredictionResultORM,
    PredictionTaskORM,
    TransactionType,
    UserORM,
    UserRole,
)
from .exceptions import NotFoundError, InsufficientBalanceError

class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_user(self, login: str, password_hash: str, role: str = UserRole.USER.value) -> UserORM:
        existing = self.session.scalar(select(UserORM).where(UserORM.login == login))
        if existing is not None:
            raise ValueError("User already exists")

        user = UserORM(login=login, password_hash=password_hash, role=role)
        user.balance = BalanceORM(credits=0)
        self.session.add(user)
        self.session.flush()
        return user

    def get_user(self, user_id: str) -> UserORM:
        user = self.session.get(UserORM, user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user