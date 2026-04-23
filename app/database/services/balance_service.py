from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import BalanceORM, BalanceTransactionORM, TransactionType

from .exceptions import InsufficientBalanceError, NotFoundError


class BalanceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _get_balance(self, user_id: str) -> BalanceORM:
        balance = self.session.get(BalanceORM, user_id)
        if balance is None:
            raise NotFoundError("Balance not found")
        return balance

    def _add_transaction(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        description: str,
    ) -> BalanceTransactionORM:
        transaction = BalanceTransactionORM(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
        )
        self.session.add(transaction)
        return transaction

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
        self._add_transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=TransactionType.TOP_UP.value,
            description=description,
        )
        self.session.flush()
        return balance

    def debit(self, user_id: str, amount: int, description: str = "balance debit") -> BalanceORM:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        balance = self._get_balance(user_id)
        if balance.credits < amount:
            raise InsufficientBalanceError("Insufficient balance")

        balance.credits -= amount
        self._add_transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=TransactionType.DEBIT.value,
            description=description,
        )
        self.session.flush()
        return balance

    def refund(self, user_id: str, amount: int, description: str = "prediction refund") -> BalanceORM:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        balance = self._get_balance(user_id)
        balance.credits += amount
        self._add_transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=TransactionType.REFUND.value,
            description=description,
        )
        self.session.flush()
        return balance
