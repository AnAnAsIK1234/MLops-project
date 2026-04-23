from pydantic import BaseModel


class HistoryItemResponse(BaseModel):
    created_at: str
    operation_type: str
    status: str
    amount: int
    description: str
    task_id: str | None = None
    model_name: str | None = None


class PredictionEventResponse(BaseModel):
    event_name: str
    details_json: str
    created_at: str