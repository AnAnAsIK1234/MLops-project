from __future__ import annotations

import os
import uvicorn
from sqlalchemy import text
from fastapi.responses import JSONResponse
from fastapi import Request

from api.fastapi_module import create_application
from database.db import Base, ENGINE, session_scope
from database.services import (
    BalanceService,
    BootstrapService,
    InsufficientBalanceError,
    ModelService,
    NotFoundError,
    PredictionService,
    UserService,
)

# app = Flask(__name__)


def bootstrap_database() -> None:
    Base.metadata.create_all(bind=ENGINE)
    with session_scope() as session:
        BootstrapService(session).seed_demo_data()


bootstrap_database()

app = create_application()


class NotFoundError(Exception):
    pass


class InsufficientBalanceError(Exception):
    pass

@app.exception_handler(NotFoundError)
async def handle_not_found(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": str(exc)}
    )


@app.exception_handler(InsufficientBalanceError)
async def handle_balance_error(request: Request, exc: InsufficientBalanceError):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )


@app.exception_handler(ValueError)
async def handle_value_error(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )

@app.post("/init-demo")
async def init_demo():
    with session_scope() as session:
        result = BootstrapService(session).seed_demo_data()
        return {"status": "ok", **result}


@app.post("/users", status_code=201)
async def create_user(request: Request):
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
async def get_user(user_id: str):
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
async def top_up(user_id: str, request: Request):
    payload = await request.json()
    with session_scope() as session:
        balance = BalanceService(session).top_up(
            user_id=user_id,
            amount=int(payload["amount"]),
            description=payload.get("description", "manual top up"),
        )
        return {"user_id": user_id, "balance": balance.credits}


@app.post("/users/{user_id}/debit")
async def debit(user_id: str, request: Request):
    payload = await request.json()
    with session_scope() as session:
        balance = BalanceService(session).debit(
            user_id=user_id,
            amount=int(payload["amount"]),
            description=payload.get("description", "manual debit"),
        )
        return {"user_id": user_id, "balance": balance.credits}


@app.get("/models")
async def list_models():
    with session_scope() as session:
        models = ModelService(session).list_models()
        return [
            {
                "id": model.id,
                "name": model.name,
                "source": model.source,
                "price_per_request": model.price_per_request,
                "is_enabled": model.is_enabled,
            }
            for model in models
        ]


@app.post("/predictions", status_code=201)
async def create_prediction(request: Request):
    payload = await request.json()
    with session_scope() as session:
        task = PredictionService(session).create_task(
            user_id=payload["user_id"],
            model_id=payload["model_id"],
            input_data=payload["input_data"],
        )
        return {"task_id": task.id, "status": task.status}


@app.post("/predictions/{task_id}/run")
def run_prediction(task_id: str):
    with session_scope() as session:
        result = PredictionService(session).run_task(task_id)
        return{
                "task_id": result.task_id,
                "output_ref": result.output_ref,
                "latency_ms": result.latency_ms,
            }


@app.get("/users/{user_id}/history")
def user_history(user_id: str):
    with session_scope() as session:
        history = PredictionService(session).user_history(user_id)
        return history


if __name__ == "__main__":
    uvicorn.run(
        # left side - file name
        # right size - variable name: app = FastAPI()
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True,
    )
