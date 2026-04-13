from __future__ import annotations

import json
from datetime import datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models import (
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


class NotFoundError(ValueError):
    pass


class InsufficientBalanceError(ValueError):
    pass


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


class BalanceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _get_balance(self, user_id: str) -> BalanceORM:
        balance = self.session.get(BalanceORM, user_id)
        if balance is None:
            raise NotFoundError("Balance not found")
        return balance

    def top_up(self, user_id: str, amount: int, description: str = "balance top up") -> BalanceORM:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        balance = self._get_balance(user_id)
        balance.credits += amount
        self.session.add(
            BalanceTransactionORM(
                user_id=user_id,
                amount=amount,
                transaction_type=TransactionType.TOP_UP.value,
                description=description,
            )
        )
        self.session.flush()
        return balance

    def debit(self, user_id: str, amount: int, description: str = "balance debit") -> BalanceORM:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        balance = self._get_balance(user_id)
        if balance.credits < amount:
            raise InsufficientBalanceError("Insufficient balance")

        balance.credits -= amount
        self.session.add(
            BalanceTransactionORM(
                user_id=user_id,
                amount=-amount,
                transaction_type=TransactionType.DEBIT.value,
                description=description,
            )
        )
        self.session.flush()
        return balance


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


class PredictionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.balance_service = BalanceService(session)
        self.model_service = ModelService(session)
        self.user_service = UserService(session)

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
