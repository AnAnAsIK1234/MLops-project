from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1] / "app" / "src"
sys.path.insert(0, str(ROOT))

from db import Base
from services import BalanceService, BootstrapService, InsufficientBalanceError, PredictionService, UserService


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        yield db
        db.commit()
    finally:
        db.close()


def test_create_user(session):
    user = UserService(session).create_user("alice", "hash")
    assert user.login == "alice"
    assert user.balance.credits == 0


def test_top_up_and_debit(session):
    user = UserService(session).create_user("bob", "hash")
    balance_service = BalanceService(session)

    balance_service.top_up(user.id, 20)
    assert user.balance.credits == 20

    balance_service.debit(user.id, 5)
    assert user.balance.credits == 15

    with pytest.raises(InsufficientBalanceError):
        balance_service.debit(user.id, 100)


def test_seed_is_idempotent(session):
    bootstrap = BootstrapService(session)
    first = bootstrap.seed_demo_data()
    second = bootstrap.seed_demo_data()

    assert first["created_users"] == 2
    assert second["created_users"] == 0


def test_prediction_flow(session):
    bootstrap = BootstrapService(session)
    bootstrap.seed_demo_data()

    user = UserService(session).create_user("carol", "hash")
    BalanceService(session).top_up(user.id, 50)
    from sqlalchemy import select
    from models import MLModelORM

    model_id = session.scalars(select(MLModelORM.id)).first()

    prediction_service = PredictionService(session)
    task = prediction_service.create_task(user.id, model_id, "hello world")
    result = prediction_service.run_task(task.id)

    history = prediction_service.user_history(user.id)
    assert result.task_id == task.id
    assert history[0]["status"] == "success"
