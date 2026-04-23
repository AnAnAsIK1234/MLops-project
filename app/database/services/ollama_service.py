from __future__ import annotations

from typing import Any

import httpx

from config import settings

from .exceptions import InferenceError


class OllamaService:
    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_MODEL
        self.timeout_sec = settings.OLLAMA_TIMEOUT_SEC
        self.temperature = settings.OLLAMA_TEMPERATURE

    def generate(self, prompt: str, model_name: str | None = None) -> dict[str, Any]:
        resolved_model = model_name or self.default_model
        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_sec,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            raise InferenceError(f"Ollama API returned an error: {detail}") from exc
        except httpx.HTTPError as exc:
            raise InferenceError(f"Ollama API request failed: {exc}") from exc

        data = response.json()
        text = (data.get("response") or "").strip()
        if not text:
            raise InferenceError("Ollama API returned an empty response")

        return {
            "text": text,
            "raw": data,
            "model": data.get("model", resolved_model),
            "response_id": data.get("created_at"),
            "done": data.get("done", True),
            "eval_count": data.get("eval_count"),
            "total_duration": data.get("total_duration"),
        }
