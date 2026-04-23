from __future__ import annotations

import os

import httpx


def generate_text(prompt: str) -> str:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    timeout_sec = float(os.getenv("OLLAMA_TIMEOUT_SEC", "180"))
    temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    with httpx.Client(timeout=timeout_sec) as client:
        response = client.post(f"{base_url}/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()

    return (data.get("response") or "").strip()