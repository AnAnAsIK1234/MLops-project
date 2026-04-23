from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, status

from api.fastapi_module import create_application
from database.db import Base, ENGINE, session_scope
from database.services import (
    BalanceService,
    BootstrapService,
    ModelService,
    PredictionService,
    UserService,
)
from src.rabbitmq import publish_message


app: FastAPI = create_application()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=ENGINE)


@app.post("/init-demo")
def init_demo() -> dict:
    with session_scope() as session:
        result = BootstrapService(session).seed_demo_data()
        return {"status": "ok", **result}


@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(request: Request) -> dict:
    payload = await request.json()
    with session_scope() as session:
        user = UserService(session).create_user(
            login=payload["login"],
            password_hash=payload.get("password_hash", "plain_text_hash"),
            role=payload.get("role", "user"),
        )
        return {
            "id": user.id,
            "login": user.login,
            "role": user.role,
            "is_active": user.is_active,
            "balance": user.balance.credits,
        }


@app.get("/users/{user_id}")
def get_user(user_id: str) -> dict:
    with session_scope() as session:
        user = UserService(session).get_user(user_id)
        return {
            "id": user.id,
            "login": user.login,
            "role": user.role,
            "is_active": user.is_active,
            "balance": user.balance.credits if user.balance else 0,
        }


@app.post("/users/{user_id}/top-up")
async def top_up(user_id: str, request: Request) -> dict:
    payload = await request.json()
    with session_scope() as session:
        balance = BalanceService(session).top_up(
            user_id=user_id,
            amount=int(payload["amount"]),
            description=payload.get("description", "manual top up"),
        )
        return {"user_id": user_id, "balance": balance.credits}


@app.post("/users/{user_id}/debit")
async def debit(user_id: str, request: Request) -> dict:
    payload = await request.json()
    with session_scope() as session:
        balance = BalanceService(session).debit(
            user_id=user_id,
            amount=int(payload["amount"]),
            description=payload.get("description", "manual debit"),
        )
        return {"user_id": user_id, "balance": balance.credits}


@app.get("/models")
def list_models() -> list[dict]:
    with session_scope() as session:
        models = ModelService(session).list_models()
        return [
            {
                "id": model.id,
                "name": model.name,
                "source": model.source,
                "provider": model.provider,
                "local_path": model.local_path,
                "price_per_request": model.price_per_request,
                "is_enabled": model.is_enabled,
            }
            for model in models
        ]


async def _enqueue_prediction(payload: dict) -> dict:
    with session_scope() as session:
        prediction_service = PredictionService(session)
        task = prediction_service.create_task(
            user_id=payload["user_id"],
            model_id=payload["model_id"],
            input_data=payload["input_data"],
        )

        try:
            publish_message({"task_id": task.id})
        except Exception as exc:
            prediction_service.fail_task(task.id, error_message=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to publish task to RabbitMQ: {exc}",
            ) from exc

        return {"task_id": task.id, "status": task.status}


@app.post("/predictions", status_code=status.HTTP_201_CREATED)
async def create_prediction(request: Request) -> dict:
    payload = await request.json()
    return await _enqueue_prediction(payload)


@app.post("/predict", status_code=status.HTTP_201_CREATED)
async def create_prediction_alias(request: Request) -> dict:
    payload = await request.json()
    return await _enqueue_prediction(payload)


@app.get("/predictions/{task_id}")
def get_prediction(task_id: str) -> dict:
    with session_scope() as session:
        service = PredictionService(session)
        task = service.get_task(task_id)
        return {
            "task_id": task.id,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None,
            "error_message": service.get_last_error(task_id),
        }


@app.get("/tasks/{task_id}")
def get_prediction_alias(task_id: str) -> dict:
    return get_prediction(task_id)


@app.post("/predictions/{task_id}/run")
def run_prediction(task_id: str) -> dict:
    with session_scope() as session:
        result = PredictionService(session).run_task(task_id)
        return {
            "task_id": result.task_id,
            "output_ref": result.output_ref,
            "latency_ms": result.latency_ms,
            "meta_json": result.meta_json,
        }


@app.get("/users/{user_id}/history")
def user_history(user_id: str) -> list[dict]:
    with session_scope() as session:
        return PredictionService(session).user_history(user_id)


@app.get("/tasks/{task_id}/history")
def task_history(task_id: str) -> list[dict]:
    with session_scope() as session:
        history = PredictionService(session).get_task_history(task_id)
        return [
            {
                "event_name": item.event_name,
                "details_json": item.details_json,
                "created_at": item.created_at.isoformat(),
            }
            for item in history
        ]
