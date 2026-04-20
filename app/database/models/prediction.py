from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base
from .enums import ModelSource, JobStatus, UserRole, TransactionType
from .user import UserORM
from .ml_model import MLModelORM


class PredictionTaskORM(Base):
    __tablename__ = "prediction_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_models.id"), nullable=False, index=True)
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.CREATED.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[UserORM] = relationship(back_populates="tasks")
    model: Mapped[MLModelORM] = relationship(back_populates="tasks")
    result: Mapped["PredictionResultORM"] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan"
    )
    history_records: Mapped[list["PredictionHistoryRecordORM"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class PredictionResultORM(Base):
    __tablename__ = "prediction_results"
    __table_args__ = (UniqueConstraint("task_id", name="uq_prediction_results_task_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("prediction_tasks.id", ondelete="CASCADE"), nullable=False)
    output_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    meta_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    task: Mapped[PredictionTaskORM] = relationship(back_populates="result")


class PredictionHistoryRecordORM(Base):
    __tablename__ = "prediction_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("prediction_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    task: Mapped[PredictionTaskORM] = relationship(back_populates="history_records")
