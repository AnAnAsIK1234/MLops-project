from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database.models import BalanceORM, MLModelORM, ModelSource, UserORM, UserRole


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

        legacy_stmt = select(MLModelORM).where(MLModelORM.provider == "gemini")
        for legacy_model in self.session.scalars(legacy_stmt):
            legacy_model.provider = "ollama"
            legacy_model.source = ModelSource.LOCAL.value
            legacy_model.local_path = settings.OLLAMA_MODEL
            legacy_model.is_enabled = True

        demo_models = [
            {
                "name": "ollama-sentiment",
                "source": ModelSource.LOCAL.value,
                "provider": "ollama",
                "local_path": settings.OLLAMA_MODEL,
                "price_per_request": 2,
                "is_enabled": True,
            },
            {
                "name": "ollama-summary",
                "source": ModelSource.LOCAL.value,
                "provider": "ollama",
                "local_path": settings.OLLAMA_MODEL,
                "price_per_request": 3,
                "is_enabled": True,
            },
        ]
        for item in demo_models:
            model = self.session.scalar(select(MLModelORM).where(MLModelORM.name == item["name"]))
            if model is None:
                self.session.add(MLModelORM(**item))
                created_models += 1
                continue

            model.source = item["source"]
            model.provider = item["provider"]
            model.local_path = item["local_path"]
            model.is_enabled = item["is_enabled"]
            model.price_per_request = item["price_per_request"]

        self.session.flush()
        return {"created_users": created_users, "created_models": created_models}
