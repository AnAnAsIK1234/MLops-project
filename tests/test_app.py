from __future__ import annotations

import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_ml_tasks.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from fastapi.testclient import TestClient

from src.app import app
from src.db import Base, ENGINE, SessionLocal
from src.models import MLTask
from src.service import mark_task_failed, mark_task_success

client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(bind=ENGINE)
    Base.metadata.create_all(bind=ENGINE)


def teardown_function() -> None:
    Base.metadata.drop_all(bind=ENGINE)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def test_predict_creates_task_and_returns_task_id(monkeypatch) -> None:
    published_messages: list[dict] = []

    def fake_publish(message: dict) -> None:
        published_messages.append(message)

    monkeypatch.setattr("src.app.publish_message", fake_publish)

    response = client.post(
        "/predict",
        json={
            "features": {"x1": 1.2, "x2": 5.7},
            "model": "demo_model",
        },
    )

    assert response.status_code == 202
    payload = response.json()

    assert "task_id" in payload
    assert payload["status"] == "queued"
    assert len(published_messages) == 1
    assert published_messages[0]["task_id"] == payload["task_id"]

    with SessionLocal() as session:
        task = session.get(MLTask, payload["task_id"])
        assert task is not None
        assert task.status == "queued"
        assert task.model == "demo_model"
        assert task.features == {"x1": 1.2, "x2": 5.7}


def test_get_task_returns_404_for_unknown_task() -> None:
    response = client.get("/tasks/unknown-task-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_get_task_returns_successful_result(monkeypatch) -> None:
    def fake_publish(message: dict) -> None:
        return None

    monkeypatch.setattr("src.app.publish_message", fake_publish)

    create_response = client.post(
        "/predict",
        json={
            "features": {"x1": 2.0, "x2": 8.0},
            "model": "demo_model",
        },
    )

    assert create_response.status_code == 202
    task_id = create_response.json()["task_id"]

    with SessionLocal() as session:
        mark_task_success(
            session,
            task_id=task_id,
            prediction=5.6,
            worker_id="worker-1",
        )
        session.commit()

    result_response = client.get(f"/tasks/{task_id}")

    assert result_response.status_code == 200
    payload = result_response.json()
    assert payload["task_id"] == task_id
    assert payload["status"] == "success"
    assert payload["prediction"] == 5.6
    assert payload["worker_id"] == "worker-1"


def test_publish_error_marks_task_as_failed(monkeypatch) -> None:
    def fake_publish(message: dict) -> None:
        raise RuntimeError("RabbitMQ unavailable")

    monkeypatch.setattr("src.app.publish_message", fake_publish)

    response = client.post(
        "/predict",
        json={
            "features": {"x1": 3.0, "x2": 4.0},
            "model": "demo_model",
        },
    )

    assert response.status_code == 500

    with SessionLocal() as session:
        tasks = session.query(MLTask).all()
        assert len(tasks) == 1
        assert tasks[0].status == "failed"