from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.db import Base

class ModelSource(str, Enum):
    API = "api"
    LOCAL = "local"


class JobStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class TransactionType(str, Enum):
    TOP_UP = "top_up"
    DEBIT = "debit"
    REFUND = "refund"
