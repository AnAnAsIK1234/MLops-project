from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MLTask(Base):
    __tablename__ = "ml_tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    features: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    prediction: Mapped[float | None] = mapped_column(Float, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )