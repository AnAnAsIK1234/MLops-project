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

class BootstrapService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def seed_demo_data(self) -> dict:
        created_users = 0
        created_models = 0

        demo_users = [
            {"login": "demo_user", "password_hash": "demo_hash", "role": UserRole.USER.value, "credits": 100},
            {"login": "demo_admin", "password_hash": "admin_hash", "role": UserRole.ADMIN.value, "credits": 500},
        ]
        for item in demo_users:
            user = self.session.scalar(select(UserORM).where(UserORM.login == item["login"]))
            if user is None:
                user = UserORM(login=item["login"], password_hash=item["password_hash"], role=item["role"])
                user.balance = BalanceORM(credits=item["credits"])
                self.session.add(user)
                created_users += 1
            elif user.balance is None:
                user.balance = BalanceORM(credits=item["credits"])
            elif user.balance.credits < item["credits"]:
                user.balance.credits = item["credits"]

        demo_models = [
            {
                "name": "sentiment-local",
                "source": ModelSource.LOCAL.value,
                "local_path": "/models/sentiment.bin",
                "price_per_request": 2,
            },
            {
                "name": "summary-api",
                "source": ModelSource.API.value,
                "provider": "openai",
                "price_per_request": 5,
            },
        ]
        for item in demo_models:
            model = self.session.scalar(select(MLModelORM).where(MLModelORM.name == item["name"]))
            if model is None:
                self.session.add(MLModelORM(**item))
                created_models += 1

        self.session.flush()
        return {"created_users": created_users, "created_models": created_models}
