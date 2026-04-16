from __future__ import annotations

import json
from datetime import datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database.models import (
    BalanceORM,
    BalanceTransactionORM,
    JobStatus,
    MLModelORM,
    ModelSource,
    PredictionHistoryRecordORM,
    PredictionResultORM,
    PredictionTaskORM,
    TransactionType,
    UserORM,
    UserRole,
)

class NotFoundError(ValueError):
    pass


class InsufficientBalanceError(ValueError):
    pass