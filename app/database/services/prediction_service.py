from __future__ import annotations

import json
from datetime import datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database.models import JobStatus, PredictionHistoryRecordORM, PredictionResultORM, PredictionTaskORM

from .balance_service import BalanceService
from .exceptions import NotFoundError
from .model_service import ModelService
from .ollama_service import OllamaService
from .user_service import UserService


class PredictionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.balance_service = BalanceService(session)
        self.model_service = ModelService(session)
        self.user_service = UserService(session)
        self.ollama_service = OllamaService()

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
                        "provider": model.provider,
                        "charged_credits": model.price_per_request,
                    },
                    ensure_ascii=False,
                ),
            )
        )
        self.session.commit()
        self.session.refresh(task)
        return task

    def run_task(self, task_id: str, worker_id: str | None = None) -> PredictionResultORM:
        task = self.session.scalar(
            select(PredictionTaskORM)
            .options(joinedload(PredictionTaskORM.model), joinedload(PredictionTaskORM.result))
            .where(PredictionTaskORM.id == task_id)
        )
        if task is None:
            raise NotFoundError("Task not found")
        if task.status == JobStatus.SUCCESS.value and task.result is not None:
            return task.result
        if task.status == JobStatus.FAILED.value:
            raise ValueError("Task is already failed")

        started = perf_counter()
        task.status = JobStatus.RUNNING.value
        task.started_at = datetime.utcnow()
        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_started",
                details_json=json.dumps(
                    {
                        "status": task.status,
                        "worker_id": worker_id,
                    },
                    ensure_ascii=False,
                ),
            )
        )
        self.session.flush()

        try:
            inference_result = self._run_model(task)
            response_text = inference_result["text"]
            output_ref = f"ollama://{task.id}"
            latency_ms = int((perf_counter() - started) * 1000)

            task.status = JobStatus.SUCCESS.value
            task.finished_at = datetime.utcnow()

            result = PredictionResultORM(
                task_id=task.id,
                output_ref=output_ref,
                latency_ms=latency_ms,
                meta_json=json.dumps(
                    {
                        "response_text": response_text,
                        "response_id": inference_result.get("response_id"),
                        "model": inference_result.get("model"),
                        "status": "success",
                        "worker_id": worker_id,
                        "provider": "ollama",
                    },
                    ensure_ascii=False,
                ),
            )
            self.session.add(result)
            self.session.add(
                PredictionHistoryRecordORM(
                    task_id=task.id,
                    event_name="task_finished",
                    details_json=json.dumps(
                        {
                            "output_ref": output_ref,
                            "latency_ms": latency_ms,
                            "response_preview": response_text[:200],
                            "worker_id": worker_id,
                            "provider": "ollama",
                        },
                        ensure_ascii=False,
                    ),
                )
            )
            self.session.commit()
            self.session.refresh(result)
            return result
        except Exception as exc:
            self._handle_task_failure(task, str(exc), worker_id=worker_id)
            self.session.commit()
            raise

    def fail_task(
        self,
        task_id: str,
        error_message: str,
        worker_id: str | None = None,
    ) -> PredictionTaskORM:
        task = self.session.scalar(
            select(PredictionTaskORM)
            .options(joinedload(PredictionTaskORM.model), joinedload(PredictionTaskORM.result))
            .where(PredictionTaskORM.id == task_id)
        )
        if task is None:
            raise NotFoundError("Task not found")
        if task.status == JobStatus.SUCCESS.value:
            raise ValueError("Cannot fail a successfully completed task")
        if task.status == JobStatus.FAILED.value:
            return task

        self._handle_task_failure(task, error_message, worker_id=worker_id)
        self.session.commit()
        self.session.refresh(task)
        return task

    def _run_model(self, task: PredictionTaskORM) -> dict:
        provider = (task.model.provider or "").lower()
        if provider != "ollama":
            raise ValueError(f"Unsupported model provider: {task.model.provider}")

        prompt = self._build_prompt(task)
        ollama_model = task.model.local_path or None
        return self.ollama_service.generate(prompt=prompt, model_name=ollama_model)

    def _build_prompt(self, task: PredictionTaskORM) -> str:
        model_name = (task.model.name or "").lower()
        if "sentiment" in model_name:
            return (
                "Определи тональность текста. Ответь строго JSON-объектом без markdown с полями "
                '"sentiment" (positive|neutral|negative) и "explanation".\n\n'
                f"Текст: {task.input_data}"
            )

        return (
            "Выполни обработку пользовательского запроса при помощи локальной LLM в Ollama. "
            "Верни краткий и полезный ответ на русском языке без markdown-заголовков.\n\n"
            f"Запрос пользователя: {task.input_data}"
        )

    def _handle_task_failure(
        self,
        task: PredictionTaskORM,
        error_message: str,
        worker_id: str | None = None,
    ) -> None:
        if task.status == JobStatus.FAILED.value:
            return

        task.status = JobStatus.FAILED.value
        task.finished_at = datetime.utcnow()

        self.balance_service.refund(
            user_id=task.user_id,
            amount=task.model.price_per_request,
            description=f"Refund for failed task {task.id}",
        )
        self.session.add(
            PredictionHistoryRecordORM(
                task_id=task.id,
                event_name="task_failed",
                details_json=json.dumps(
                    {
                        "error": error_message,
                        "refunded_credits": task.model.price_per_request,
                        "worker_id": worker_id,
                        "provider": "ollama",
                    },
                    ensure_ascii=False,
                ),
            )
        )
        self.session.flush()

    def get_last_error(self, task_id: str) -> str | None:
        stmt = (
            select(PredictionHistoryRecordORM)
            .where(
                PredictionHistoryRecordORM.task_id == task_id,
                PredictionHistoryRecordORM.event_name == "task_failed",
            )
            .order_by(PredictionHistoryRecordORM.created_at.desc())
        )
        record = self.session.scalar(stmt)
        if record is None:
            return None
        try:
            data = json.loads(record.details_json)
        except json.JSONDecodeError:
            return record.details_json
        return data.get("error")

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
