from __future__ import annotations

from sqlalchemy.orm import Session

from src.models import MLTask
from src.schemas import PredictRequest


def create_task(session: Session, task_id: str, payload: PredictRequest) -> MLTask:
    task = MLTask(
        task_id=task_id,
        model=payload.model,
        features=payload.features.model_dump(),
        status="queued",
        prediction=None,
        worker_id=None,
    )
    session.add(task)
    session.flush()
    session.refresh(task)
    return task


def get_task_by_id(session: Session, task_id: str) -> MLTask | None:
    return session.get(MLTask, task_id)


def mark_task_processing(session: Session, task_id: str, worker_id: str) -> MLTask | None:
    task = get_task_by_id(session, task_id)
    if task is None:
        return None

    task.status = "processing"
    task.worker_id = worker_id
    session.add(task)
    session.flush()
    session.refresh(task)
    return task


def mark_task_success(
    session: Session,
    task_id: str,
    prediction: float,
    worker_id: str,
) -> MLTask | None:
    task = get_task_by_id(session, task_id)
    if task is None:
        return None

    task.status = "success"
    task.prediction = prediction
    task.worker_id = worker_id
    session.add(task)
    session.flush()
    session.refresh(task)
    return task


def mark_task_failed(session: Session, task_id: str, worker_id: str | None = None) -> MLTask | None:
    task = get_task_by_id(session, task_id)
    if task is None:
        return None

    task.status = "failed"
    if worker_id is not None:
        task.worker_id = worker_id
    session.add(task)
    session.flush()
    session.refresh(task)
    return task