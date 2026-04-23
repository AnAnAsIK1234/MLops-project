from __future__ import annotations

from database.services.balance_service import BalanceService
from database.services.prediction_service import PredictionService


class HistoryService:
    def __init__(self, session) -> None:
        self.session = session
        self.balance_service = BalanceService(session)
        self.prediction_service = PredictionService(session)

    def get_user_history(self, user_id: str) -> list[dict]:
        items: list[dict] = []

        for tx in self.balance_service.get_transactions(user_id):
            items.append(
                {
                    "created_at": tx.created_at.isoformat(),
                    "operation_type": tx.transaction_type,
                    "status": "success",
                    "amount": tx.amount,
                    "description": tx.description,
                    "task_id": None,
                    "model_name": None,
                }
            )

        for item in self.prediction_service.user_prediction_history(user_id):
            items.append(
                {
                    "created_at": item["created_at"],
                    "operation_type": "prediction",
                    "status": item["status"],
                    "amount": item["charged_credits"],
                    "description": f"Prediction via model {item['model_name']}",
                    "task_id": item["task_id"],
                    "model_name": item["model_name"],
                }
            )

        items.sort(key=lambda x: x["created_at"], reverse=True)
        return items