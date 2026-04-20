from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class BaseORMSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)