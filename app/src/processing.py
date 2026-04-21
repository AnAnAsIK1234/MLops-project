from __future__ import annotations

from src.schemas import TaskMessage


def validate_task_message(payload: dict) -> TaskMessage:
    return TaskMessage.model_validate(payload)


def run_mock_prediction(task: TaskMessage) -> float:
    x1 = task.features.x1
    x2 = task.features.x2

    prediction = (x1 * 0.4) + (x2 * 0.6)
    return round(prediction, 4)