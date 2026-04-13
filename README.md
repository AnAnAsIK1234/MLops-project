# ORM reference solution for the assignment

## What is included
- Flask application with SQLAlchemy ORM
- PostgreSQL connection via environment variables
- Tables: users, balances, balance_transactions, ml_models, prediction_tasks, prediction_results, prediction_history
- Idempotent demo-data initialization
- Basic HTTP endpoints for creating users, topping up/debiting balance, creating prediction tasks, running them, and reading history
- Pytest tests for core scenarios

## Run locally with Docker Compose
1. Copy `app/.env.example` to `app/.env`
2. Run `docker compose up --build`
3. Open `http://localhost/health`

## Main endpoints
- `POST /init-demo`
- `POST /users`
- `GET /users/<user_id>`
- `POST /users/<user_id>/top-up`
- `POST /users/<user_id>/debit`
- `GET /models`
- `POST /predictions`
- `POST /predictions/<task_id>/run`
- `GET /users/<user_id>/history`
