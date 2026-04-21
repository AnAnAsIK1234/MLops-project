from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from src.db import Base, ENGINE, get_db
from src.rabbitmq import publish_message
from src.schemas import (
    PredictAcceptedResponse,
    PredictRequest,
    TaskMessage,
    TaskResultResponse,
)
from src.service import create_task, get_task_by_id, mark_task_failed

app = FastAPI(title="ML Tasks Service")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=ENGINE)


@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.post(
    "/predict",
    response_model=PredictAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def predict(payload: PredictRequest, db: Session = Depends(get_db)) -> PredictAcceptedResponse:
    task_id = str(uuid4())

    task = create_task(db, task_id=task_id, payload=payload)
    db.commit()
    db.refresh(task)

    message = TaskMessage(
        task_id=task_id,
        features=payload.features,
        model=payload.model,
        timestamp=datetime.now(timezone.utc),
    )

    try:
        publish_message(message.model_dump(mode="json"))
    except Exception as exc:
        mark_task_failed(db, task_id=task_id)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish task to RabbitMQ: {exc}",
        ) from exc

    return PredictAcceptedResponse(task_id=task_id)


@app.get("/tasks/{task_id}", response_model=TaskResultResponse)
def get_task(task_id: str, db: Session = Depends(get_db)) -> TaskResultResponse:
    task = get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return TaskResultResponse.model_validate(task)