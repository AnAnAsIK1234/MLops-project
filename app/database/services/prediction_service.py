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
from .user_service import UserService
from .balance_service import BalanceService
from .model_service import ModelService

class PredictionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.balance_service = BalanceService(session)
        self.model_service = ModelService(session)
        self.user_service = UserService(session)

<<<<<<< HEAD
    def get_task(self, task_id: str) -> PredictionTaskORM:
        task = self.session.get(PredictionTaskORM, task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task

    def get_task_history(self, task_id: str) -> list[PredictionHistoryRecordORM]:
        task = self.get_task(task_id)
        stmt = (
            select(PredictionHistoryRecordORM)
            .where(PredictionHistoryRecordORM.task_id == task.id)
            .order_by(PredictionHistoryRecordORM.created_at.asc())
        )
        return list(self.session.scalars(stmt))
    
=======
>>>>>>> origin/hw3
    def create_task(self, user_id: str, model_id: str, input_data: str) -> PredictionTaskORM:
        user = self.user_service.get_user(user_id)
        if not user.is_active:
            raise ValueError("User is inactive")

        model = self.model_service.get_enabled_model(model_id)
        self.balance_service.debit(user_id, model.price_per_request, f"Charge for model {model.name}")

        task = PredictionTaskORM(
            user_id=user_id,
            model_id=model_id,
            input_data=input_data,
            status=JobStatus.PENDING.value,
        )
        self.session.add(task)
        self.session.flush()

        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_created",
                details_json=json.dumps(
                    {
                        "model_name": model.name,
                        "charged_credits": model.price_per_request,
                    }
                ),
            )
        )
        self.session.flush()
        return task

    def run_task(self, task_id: str) -> PredictionResultORM:
        task = self.session.get(PredictionTaskORM, task_id)
        if task is None:
            raise NotFoundError("Task not found")
        if task.status == JobStatus.SUCCESS.value and task.result is not None:
            return task.result

        started = perf_counter()
        task.status = JobStatus.RUNNING.value
        task.started_at = datetime.utcnow()
        self.session.flush()
        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_started",
                details_json=json.dumps({"status": task.status}),
            )
        )

        output_ref = f"prediction://{task.id}"
        latency_ms = int((perf_counter() - started) * 1000)
        task.status = JobStatus.SUCCESS.value
        task.finished_at = datetime.utcnow()

        result = PredictionResultORM(
            task_id=task.id,
            output_ref=output_ref,
            latency_ms=latency_ms,
            meta_json=json.dumps({"input_preview": task.input_data[:50], "status": "success"}),
        )
        self.session.add(result)
        self.session.flush()

        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_finished",
                details_json=json.dumps({"output_ref": output_ref, "latency_ms": latency_ms}),
            )
        )
        self.session.flush()
        return result

    def user_history(self, user_id: str) -> list[dict]:
        tasks = list(
            self.session.scalars(
                select(PredictionTaskORM)
                .options(joinedload(PredictionTaskORM.model), joinedload(PredictionTaskORM.result))
                .where(PredictionTaskORM.user_id == user_id)
                .order_by(PredictionTaskORM.created_at.desc())
            )
        )

        history: list[dict] = []
        for task in tasks:
            history.append(
                {
                    "task_id": task.id,
                    "created_at": task.created_at.isoformat(),
                    "status": task.status,
                    "model_name": task.model.name,
                    "input_data": task.input_data,
                    "output_ref": task.result.output_ref if task.result else None,
                    "latency_ms": task.result.latency_ms if task.result else None,
                    "price_per_request": task.model.price_per_request,
                }
            )
        return history
