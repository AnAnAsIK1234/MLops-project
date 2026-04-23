from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_from_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "ML Tasks Service")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    debug: bool = _bool_from_env("DEBUG", False)

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://app_user:app_password@database:5432/app_db",
    )

    rabbitmq_url: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@rabbitmq:5672/%2F",
    )
    rabbitmq_queue: str = os.getenv("RABBITMQ_QUEUE", "ml_tasks")
    rabbitmq_exchange: str = os.getenv("RABBITMQ_EXCHANGE", "")
    rabbitmq_routing_key: str = os.getenv("RABBITMQ_ROUTING_KEY", "ml_tasks")
    rabbitmq_durable: bool = _bool_from_env("RABBITMQ_DURABLE", True)
    rabbitmq_connection_attempts: int = int(os.getenv("RABBITMQ_CONNECTION_ATTEMPTS", "30"))
    rabbitmq_retry_delay_sec: int = int(os.getenv("RABBITMQ_RETRY_DELAY_SEC", "2"))

    worker_prefetch_count: int = int(os.getenv("WORKER_PREFETCH_COUNT", "1"))
    worker_simulated_delay_sec: float = float(os.getenv("WORKER_SIMULATED_DELAY_SEC", "1.0"))
    worker_id: str = os.getenv("WORKER_ID", "worker-unknown")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    ollama_timeout_sec: float = float(os.getenv("OLLAMA_TIMEOUT_SEC", "180"))
    ollama_temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))


settings = Settings()
