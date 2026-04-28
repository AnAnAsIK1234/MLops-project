from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from database.services.prediction_service import PredictionService


def test_full_success_flow_debits_balance_and_writes_history(
    client: TestClient,
    auth_headers: dict[str, str],
    model_id: str,
    db_session: Session,
    monkeypatch,
) -> None:
    published_messages: list[dict] = []

    def fake_publish(message: dict) -> None:
        published_messages.append(message)

    monkeypatch.setattr("routes.predict.publish_message", fake_publish)

    top_up_response = client.post(
        "/balance/top-up",
        headers=auth_headers,
        json={"amount": 10},
    )
    assert top_up_response.status_code == 200

    predict_response = client.post(
        "/predict/form",
        headers=auth_headers,
        json={
            "model_id": model_id,
            "prompt": "Make a forecast",
        },
    )
    assert predict_response.status_code == 202

    payload = predict_response.json()
    task_id = payload["task_id"]

    assert payload["status"] == "pending"
    assert payload["processed_count"] == 1
    assert payload["rejected_count"] == 0
    assert published_messages == [{"task_id": task_id}]

    service = PredictionService(db_session)
    service.start_task(task_id)
    service.complete_task_success(
        task_id,
        result_payload=[
            {
                "input": {"prompt": "Make a forecast"},
                "response": "ok",
            }
        ],
        summary_payload={
            "processed_count": 1,
            "backend": "test",
        },
    )
    db_session.commit()

    result_response = client.get(
        f"/predict/{task_id}",
        headers=auth_headers,
    )
    assert result_response.status_code == 200

    result = result_response.json()
    assert result["task_id"] == task_id
    assert result["status"] == "success"
    assert result["charged_credits"] == 2
    assert result["result"][0]["response"] == "ok"

    balance_response = client.get("/balance/", headers=auth_headers)
    assert balance_response.status_code == 200
    assert balance_response.json()["credits"] == 8

    history_response = client.get("/history/", headers=auth_headers)
    assert history_response.status_code == 200

    history = history_response.json()
    operation_types = {item["operation_type"] for item in history}

    assert "top_up" in operation_types
    assert "debit" in operation_types
    assert "prediction" in operation_types
    assert any(
        item["task_id"] == task_id and item["status"] == "success"
        for item in history
    )

    events_response = client.get(
        f"/history/predictions/{task_id}",
        headers=auth_headers,
    )
    assert events_response.status_code == 200

    event_names = {item["event_name"] for item in events_response.json()}
    assert "task_created" in event_names
    assert "task_started" in event_names
    assert "task_finished" in event_names


def test_prediction_is_rejected_when_balance_is_not_enough(
    client: TestClient,
    auth_headers: dict[str, str],
    model_id: str,
    monkeypatch,
) -> None:
    published_messages: list[dict] = []

    def fake_publish(message: dict) -> None:
        published_messages.append(message)

    monkeypatch.setattr("routes.predict.publish_message", fake_publish)

    response = client.post(
        "/predict/form",
        headers=auth_headers,
        json={
            "model_id": model_id,
            "prompt": "Request without balance",
        },
    )

    assert response.status_code == 402
    assert response.json()["detail"] == "Insufficient balance"
    assert published_messages == []

    balance_response = client.get("/balance/", headers=auth_headers)
    assert balance_response.status_code == 200
    assert balance_response.json()["credits"] == 0


def test_worker_failure_does_not_debit_balance(
    client: TestClient,
    auth_headers: dict[str, str],
    model_id: str,
    db_session: Session,
    monkeypatch,
) -> None:
    def fake_publish(message: dict) -> None:
        return None

    monkeypatch.setattr("routes.predict.publish_message", fake_publish)

    top_up_response = client.post(
        "/balance/top-up",
        headers=auth_headers,
        json={"amount": 10},
    )
    assert top_up_response.status_code == 200

    predict_response = client.post(
        "/predict/form",
        headers=auth_headers,
        json={
            "model_id": model_id,
            "prompt": "ML-query with mistake",
        },
    )
    assert predict_response.status_code == 202

    task_id = predict_response.json()["task_id"]

    service = PredictionService(db_session)
    service.start_task(task_id)
    service.complete_task_failed(task_id, "Ollama error")
    db_session.commit()

    result_response = client.get(
        f"/predict/{task_id}",
        headers=auth_headers,
    )
    assert result_response.status_code == 200

    result = result_response.json()
    assert result["status"] == "failed"
    assert result["charged_credits"] == 0
    assert result["error_message"] == "Ollama error"

    balance_response = client.get("/balance/", headers=auth_headers)
    assert balance_response.status_code == 200
    assert balance_response.json()["credits"] == 10


def test_publish_error_marks_task_failed_and_does_not_debit_balance(
    client: TestClient,
    auth_headers: dict[str, str],
    model_id: str,
    monkeypatch,
) -> None:
    def fake_publish(message: dict) -> None:
        raise RuntimeError("RabbitMQ unavailable")

    monkeypatch.setattr("routes.predict.publish_message", fake_publish)

    top_up_response = client.post(
        "/balance/top-up",
        headers=auth_headers,
        json={"amount": 10},
    )
    assert top_up_response.status_code == 200

    response = client.post(
        "/predict/form",
        headers=auth_headers,
        json={
            "model_id": model_id,
            "prompt": "With request will drop",
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to publish task to queue"

    balance_response = client.get("/balance/", headers=auth_headers)
    assert balance_response.status_code == 200
    assert balance_response.json()["credits"] == 10

    prediction_history_response = client.get(
        "/history/predictions",
        headers=auth_headers,
    )
    assert prediction_history_response.status_code == 200

    prediction_history = prediction_history_response.json()
    assert len(prediction_history) == 1
    assert prediction_history[0]["status"] == "failed"
    assert prediction_history[0]["charged_credits"] == 0


def test_file_prediction_accepts_partially_valid_csv(
    client: TestClient,
    auth_headers: dict[str, str],
    model_id: str,
    monkeypatch,
) -> None:
    published_messages: list[dict] = []

    def fake_publish(message: dict) -> None:
        published_messages.append(message)

    monkeypatch.setattr("routes.predict.publish_message", fake_publish)

    client.post(
        "/balance/top-up",
        headers=auth_headers,
        json={"amount": 10},
    )

    csv_content = "prompt,extra\nvalid prompt,1\n,2\n"

    response = client.post(
        "/predict/file",
        headers=auth_headers,
        data={"model_id": model_id},
        files={
            "file": (
                "prompts.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 202

    payload = response.json()
    assert payload["processed_count"] == 1
    assert payload["rejected_count"] == 1
    assert payload["validation_errors"][0]["row_number"] == 2
    assert len(published_messages) == 1