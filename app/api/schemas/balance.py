from datetime import datetime
from pydantic import BaseModel, Field


class BalanceResponse(BaseModel):
    user_id: str
    credits: int
    updated_at: datetime | None = None


class TopUpRequest(BaseModel):
    amount: int = Field(..., gt=0, le=1_000_000)
    description: str | None = Field(default="balance top up", max_length=255)


class TransactionResponse(BaseModel):
    id: str
    amount: int
    transaction_type: str
    description: str
    created_at: datetime