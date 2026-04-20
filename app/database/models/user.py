from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

from .enums import ModelSource, JobStatus, UserRole, TransactionType

class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    balance: Mapped["BalanceORM"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    tasks: Mapped[list["PredictionTaskORM"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[list["BalanceTransactionORM"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )