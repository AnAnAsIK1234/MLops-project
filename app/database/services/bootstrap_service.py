from __future__ import annotations

from sqlalchemy import select

from database.models import MLModelORM, ModelSource


class BootstrapService:
    def __init__(self, session) -> None:
        self.session = session

    def seed_demo_data(self) -> dict:
        created_models = 0

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
        return {"created_models": created_models}