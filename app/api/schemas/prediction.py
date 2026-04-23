from pydantic import BaseModel, Field


class PredictFormRequest(BaseModel):
    model_id: str = Field(..., min_length=1, max_length=36)
    x1: float
    x2: float


class ValidationErrorItem(BaseModel):
    row_number: int
    raw_data: dict
    error_message: str


class PredictAcceptedResponse(BaseModel):
    task_id: str
    status: str
    processed_count: int
    rejected_count: int
    charged_credits: int | None = None
    validation_errors: list[ValidationErrorItem] = []


class PredictResultResponse(BaseModel):
    task_id: str
    status: str
    charged_credits: int
    processed_count: int
    rejected_count: int
    result: list[dict]
    summary: dict
    error_message: str | None = None


class PredictionHistoryItem(BaseModel):
    task_id: str
    created_at: str
    status: str
    model_name: str
    charged_credits: int
    processed_count: int
    rejected_count: int
    error_message: str | None = None