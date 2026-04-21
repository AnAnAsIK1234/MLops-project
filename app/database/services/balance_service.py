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
from .exceptions import NotFoundError, InsufficientBalanceError
class BalanceService:
    def __init__(self, session) -> None:
        self.session = session

    def _get_balance(self, user_id: str) -> BalanceORM:
        balance = self.session.get(BalanceORM, user_id)
        if balance is None:
            raise NotFoundError("Balance not found")
        return balance

    def get_balance(self, user_id: str) -> BalanceORM:
        return self._get_balance(user_id)

    def get_transactions(self, user_id: str) -> list[BalanceTransactionORM]:
        stmt = (
            select(BalanceTransactionORM)
            .where(BalanceTransactionORM.user_id == user_id)
            .order_by(BalanceTransactionORM.created_at.desc())
        )
        return list(self.session.scalars(stmt))

    def top_up(self, user_id: str, amount: int, description: str = "balance top up") -> BalanceORM:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        balance = self._get_balance(user_id)
        balance.credits += amount
        self.session.add(
            BalanceTransactionORM(
                user_id=user_id,
                amount=amount,
                transaction_type="top_up",
                description=description,
            )
        )
        self.session.flush()
        return balance
