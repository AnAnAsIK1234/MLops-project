from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(ROOT))

from database.db import Base
from database.models import BalanceTransactionORM, MLModelORM, PredictionTaskORM
from database.services import BalanceService, BootstrapService, PredictionService, UserService


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


def test_worker_failure_refunds_credits(session):
    BootstrapService(session).seed_demo_data()

    user = UserService(session).create_user("worker_refund_user", "hash")
    BalanceService(session).top_up(user.id, 20, "top up for test")
    session.commit()

    model_id = session.scalars(select(MLModelORM.id)).first()
    prediction_service = PredictionService(session)

    task = prediction_service.create_task(user.id, model_id, "test prompt")
    balance_after_debit = BalanceService(session).get_balance(user.id).credits

    def _boom(prompt: str, model_name: str | None = None) -> dict:
        raise RuntimeError("model crashed")

    prediction_service.gemini_service.generate = _boom  # type: ignore[method-assign]

    with pytest.raises(RuntimeError):
        prediction_service.run_task(task.id, worker_id="worker-1")

    failed_task = session.get(PredictionTaskORM, task.id)
    assert failed_task is not None
    assert failed_task.status == "failed"

    balance_after_refund = BalanceService(session).get_balance(user.id).credits
    assert balance_after_refund > balance_after_debit
    assert balance_after_refund == 20

    refund_tx = session.scalars(
        select(BalanceTransactionORM)
        .where(BalanceTransactionORM.user_id == user.id)
        .order_by(BalanceTransactionORM.created_at.desc())
    ).first()
    assert refund_tx is not None
    assert refund_tx.transaction_type == "refund"

    history = prediction_service.get_task_history(task.id)
    task_failed = history[-1]
    assert task_failed.event_name == "task_failed"
    details = json.loads(task_failed.details_json)
    assert details["refunded_credits"] > 0
    assert details["worker_id"] == "worker-1"


def test_fail_task_is_idempotent_and_does_not_double_refund(session):
    BootstrapService(session).seed_demo_data()

    user = UserService(session).create_user("worker_refund_user_2", "hash")
    BalanceService(session).top_up(user.id, 20, "top up for test")
    session.commit()

    model_id = session.scalars(select(MLModelORM.id)).first()
    prediction_service = PredictionService(session)
    task = prediction_service.create_task(user.id, model_id, "test prompt")

    prediction_service.fail_task(task.id, "rabbitmq publish failed", worker_id="publisher")
    balance_after_first_refund = BalanceService(session).get_balance(user.id).credits

    prediction_service.fail_task(task.id, "duplicate failure", worker_id="publisher")
    balance_after_second_refund = BalanceService(session).get_balance(user.id).credits

    assert balance_after_first_refund == 20
    assert balance_after_second_refund == 20
