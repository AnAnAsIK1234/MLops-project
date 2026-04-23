from datetime import datetime

from pydantic import BaseModel


class ModelResponse(BaseModel):
    id: str
    name: str
    source: str
    price_per_request: int
    is_enabled: bool
    created_at: datetime