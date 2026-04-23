from __future__ import annotations

import re

import httpx

from src.config import settings
from src.schemas import TaskMessage


FLOAT_RE = re.compile(r"[-+]?\d+(?:[\.,]\d+)?")


def validate_task_message(payload: dict) -> TaskMessage:
    return TaskMessage.model_validate(payload)


def run_model_prediction(task: TaskMessage) -> float:
    prompt = (
        "You are a regression model. Based on the numeric features below, return only one floating-point "
        "number without explanation.\n"
        f"x1={task.features.x1}\n"
        f"x2={task.features.x2}"
    )
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": settings.ollama_temperature},
    }
    response = httpx.post(
        f"{settings.ollama_base_url.rstrip('/')}/api/generate",
        json=payload,
        timeout=settings.ollama_timeout_sec,
    )
    response.raise_for_status()
    text = (response.json().get("response") or "").strip()
    if not text:
        raise ValueError("Ollama returned an empty response")

    match = FLOAT_RE.search(text)
    if match is None:
        raise ValueError(f"Could not parse float from Ollama response: {text}")

    return round(float(match.group(0).replace(",", ".")), 4)
