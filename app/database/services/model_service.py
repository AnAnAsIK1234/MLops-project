from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import MLModelORM

from .exceptions import NotFoundError


class ModelService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_models(self) -> list[MLModelORM]:
        return list(self.session.scalars(select(MLModelORM).order_by(MLModelORM.name.asc())))

    def get_enabled_model(self, model_id: str) -> MLModelORM:
        model = self.session.get(MLModelORM, model_id)
        if model is None:
            raise NotFoundError("Model not found")
        if not model.is_enabled:
            raise ValueError("Model is disabled")
        return model
