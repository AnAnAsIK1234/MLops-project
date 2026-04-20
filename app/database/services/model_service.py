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