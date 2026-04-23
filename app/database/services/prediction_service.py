from __future__ import annotations

import json
from datetime import datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.models import (
    JobStatus,
    PredictionHistoryRecordORM,
    PredictionResultORM,
    PredictionTaskORM,
    PredictionValidationErrorORM,
    RequestSource,
)
from .balance_service import BalanceService
from .exceptions import InsufficientBalanceError, NotFoundError
from .model_service import ModelService
from .user_service import UserService


class PredictionService:
    def __init__(self, session) -> None:
        self.session = session
        self.balance_service = BalanceService(session)
        self.model_service = ModelService(session)
        self.user_service = UserService(session)

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

    def save_validation_errors(self, task_id: str, errors: list[dict]) -> None:
        for item in errors:
            self.session.add(
                PredictionValidationErrorORM(
                    task_id=task_id,
                    row_number=item["row_number"],
                    raw_data=json.dumps(item["raw_data"], ensure_ascii=False),
                    error_message=item["error_message"],
                )
            )
        self.session.flush()

    def create_task(
        self,
        user_id: str,
        model_id: str,
        valid_records: list[dict],
        invalid_records: list[dict],
        request_source: str,
        source_filename: str | None = None,
    ) -> PredictionTaskORM:
        user = self.user_service.get_user(user_id)
        if not user.is_active:
            raise ValueError("User is inactive")

        model = self.model_service.get_enabled_model(model_id)
        balance = self.balance_service.get_balance(user_id)

        if balance.credits < model.price_per_request:
            raise InsufficientBalanceError("Insufficient balance")

        task = PredictionTaskORM(
            user_id=user_id,
            model_id=model_id,
            input_data=json.dumps(valid_records, ensure_ascii=False),
            request_source=request_source,
            source_filename=source_filename,
            total_records=len(valid_records) + len(invalid_records),
            valid_records=len(valid_records),
            invalid_records=len(invalid_records),
            status=JobStatus.PENDING.value,
        )
        self.session.add(task)
        self.session.flush()

        if invalid_records:
            self.save_validation_errors(task.id, invalid_records)

        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_created",
                details_json=json.dumps(
                    {
                        "model_id": model.id,
                        "model_name": model.name,
                        "valid_records": len(valid_records),
                        "invalid_records": len(invalid_records),
                    },
                    ensure_ascii=False,
                ),
            )
        )
        self.session.flush()
        return task

    def start_task(self, task_id: str) -> PredictionTaskORM:
        task = self.get_task(task_id)
        task.status = JobStatus.RUNNING.value
        task.started_at = datetime.utcnow()

        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_started",
                details_json=json.dumps({"status": task.status}),
            )
        )
        self.session.flush()
        return task

    def complete_task_success(self, task_id: str, result_payload: list[dict], summary_payload: dict) -> PredictionResultORM:
        started = perf_counter()

        task = self.get_task(task_id)
        model = self.model_service.get_enabled_model(task.model_id)

        self.balance_service.debit(
            user_id=task.user_id,
            amount=model.price_per_request,
            description=f"Charge for model {model.name}",
        )

        task.status = JobStatus.SUCCESS.value
        task.finished_at = datetime.utcnow()
        task.charged_credits = model.price_per_request

        latency_ms = int((perf_counter() - started) * 1000)

        result = PredictionResultORM(
            task_id=task.id,
            output_json=json.dumps(result_payload, ensure_ascii=False),
            summary_json=json.dumps(summary_payload, ensure_ascii=False),
            latency_ms=latency_ms,
        )
        self.session.add(result)

        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_finished",
                details_json=json.dumps(
                    {
                        "charged_credits": model.price_per_request,
                        "latency_ms": latency_ms,
                    }
                ),
            )
        )
        self.session.flush()
        return result

    def complete_task_failed(self, task_id: str, error_message: str) -> PredictionTaskORM:
        task = self.get_task(task_id)
        task.status = JobStatus.FAILED.value
        task.finished_at = datetime.utcnow()
        task.error_message = error_message

        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_failed",
                details_json=json.dumps({"error_message": error_message}, ensure_ascii=False),
            )
        )
        self.session.flush()
        return task

    def user_prediction_history(self, user_id: str) -> list[dict]:
        tasks = list(
            self.session.scalars(
                select(PredictionTaskORM)
                .options(joinedload(PredictionTaskORM.model))
                .where(PredictionTaskORM.user_id == user_id)
                .order_by(PredictionTaskORM.created_at.desc())
            )
        )

        items: list[dict] = []
        for task in tasks:
            items.append(
                {
                    "task_id": task.id,
                    "created_at": task.created_at.isoformat(),
                    "status": task.status,
                    "model_name": task.model.name,
                    "charged_credits": task.charged_credits,
                    "processed_count": task.valid_records,
                    "rejected_count": task.invalid_records,
                    "error_message": task.error_message,
                }
            )
        return items