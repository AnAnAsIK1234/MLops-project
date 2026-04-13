from __future__ import annotations

import os

from flask import Flask, jsonify, request
from sqlalchemy import text

from db import Base, ENGINE, session_scope
from services import (
    BalanceService,
    BootstrapService,
    InsufficientBalanceError,
    ModelService,
    NotFoundError,
    PredictionService,
    UserService,
)

app = Flask(__name__)


def bootstrap_database() -> None:
    Base.metadata.create_all(bind=ENGINE)
    with session_scope() as session:
        BootstrapService(session).seed_demo_data()


bootstrap_database()


@app.errorhandler(NotFoundError)
def handle_not_found(error: NotFoundError):
    return jsonify({"error": str(error)}), 404


@app.errorhandler(InsufficientBalanceError)
def handle_balance_error(error: InsufficientBalanceError):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(ValueError)
def handle_value_error(error: ValueError):
    return jsonify({"error": str(error)}), 400


@app.route("/")
def index():
    return jsonify(
        {
            "message": "ML ORM service is running",
            "app_port": os.getenv("APP_PORT", "8000"),
            "database_url": os.getenv("DATABASE_URL", "postgresql via env variables"),
        }
    )


@app.route("/health")
def health():
    with ENGINE.connect() as connection:
        connection.execute(text("SELECT 1"))
    return jsonify({"status": "ok"})


@app.post("/init-demo")
def init_demo():
    with session_scope() as session:
        result = BootstrapService(session).seed_demo_data()
        return jsonify({"status": "ok", **result})


@app.post("/users")
def create_user():
    payload = request.get_json(force=True)
    with session_scope() as session:
        user = UserService(session).create_user(
            login=payload["login"],
            password_hash=payload.get("password_hash", "plain_text_hash"),
            role=payload.get("role", "user"),
        )
        return (
            jsonify(
                {
                    "id": user.id,
                    "login": user.login,
                    "role": user.role,
                    "is_active": user.is_active,
                    "balance": user.balance.credits,
                }
            ),
            201,
        )


@app.get("/users/<user_id>")
def get_user(user_id: str):
    with session_scope() as session:
        user = UserService(session).get_user(user_id)
        return jsonify(
            {
                "id": user.id,
                "login": user.login,
                "role": user.role,
                "is_active": user.is_active,
                "balance": user.balance.credits if user.balance else 0,
            }
        )


@app.post("/users/<user_id>/top-up")
def top_up(user_id: str):
    payload = request.get_json(force=True)
    with session_scope() as session:
        balance = BalanceService(session).top_up(
            user_id=user_id,
            amount=int(payload["amount"]),
            description=payload.get("description", "manual top up"),
        )
        return jsonify({"user_id": user_id, "balance": balance.credits})


@app.post("/users/<user_id>/debit")
def debit(user_id: str):
    payload = request.get_json(force=True)
    with session_scope() as session:
        balance = BalanceService(session).debit(
            user_id=user_id,
            amount=int(payload["amount"]),
            description=payload.get("description", "manual debit"),
        )
        return jsonify({"user_id": user_id, "balance": balance.credits})


@app.get("/models")
def list_models():
    with session_scope() as session:
        models = ModelService(session).list_models()
        return jsonify(
            [
                {
                    "id": model.id,
                    "name": model.name,
                    "source": model.source,
                    "price_per_request": model.price_per_request,
                    "is_enabled": model.is_enabled,
                }
                for model in models
            ]
        )


@app.post("/predictions")
def create_prediction():
    payload = request.get_json(force=True)
    with session_scope() as session:
        task = PredictionService(session).create_task(
            user_id=payload["user_id"],
            model_id=payload["model_id"],
            input_data=payload["input_data"],
        )
        return jsonify({"task_id": task.id, "status": task.status}), 201


@app.post("/predictions/<task_id>/run")
def run_prediction(task_id: str):
    with session_scope() as session:
        result = PredictionService(session).run_task(task_id)
        return jsonify(
            {
                "task_id": result.task_id,
                "output_ref": result.output_ref,
                "latency_ms": result.latency_ms,
            }
        )


@app.get("/users/<user_id>/history")
def user_history(user_id: str):
    with session_scope() as session:
        history = PredictionService(session).user_history(user_id)
        return jsonify(history)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("APP_PORT", 8000)))
