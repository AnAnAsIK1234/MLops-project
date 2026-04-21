from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FeaturesPayload(BaseModel):
    x1: float = Field(..., description="First numeric feature")
    x2: float = Field(..., description="Second numeric feature")


class PredictRequest(BaseModel):
    features: FeaturesPayload
    model: str = Field(..., min_length=1, description="Model name")


class TaskMessage(BaseModel):
    task_id: str
    features: FeaturesPayload
    model: str
    timestamp: datetime


class PredictAcceptedResponse(BaseModel):
    task_id: str
    status: Literal["queued"] = "queued"


class TaskResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    model: str
    status: str
    prediction: float | None = None
    worker_id: str | None = None
    created_at: datetime
    updated_at: datetime