from datetime import datetime
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    model_id: str = Field(..., min_length=1, max_length=36)
    input_data: str = Field(..., min_length=1)


class PredictResponse(BaseModel):
    task_id: str
    status: str
    output_ref: str | None = None
    latency_ms: int | None = None
    charged_credits: int | None = None


class PredictionHistoryItem(BaseModel):
    task_id: str
    created_at: str
    status: str
    model_name: str
    input_data: str
    output_ref: str | None
    latency_ms: int | None
    price_per_request: int