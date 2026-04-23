from pydantic import BaseModel


class PredictionEventResponse(BaseModel):
    event_name: str
    details_json: str
    created_at: str