from fastapi import APIRouter, Depends

from api.dependencies import get_current_user, get_db
from api.schemas.model import ModelResponse
from database.models import UserORM
from database.services.model_service import ModelService

models_router = APIRouter(prefix="/models", tags=["Models"])


@models_router.get("/", response_model=list[ModelResponse])
def list_models(
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    service = ModelService(db)
    items = service.list_models()
    return [
        ModelResponse(
            id=item.id,
            name=item.name,
            source=item.source,
            price_per_request=item.price_per_request,
            is_enabled=item.is_enabled,
            created_at=item.created_at,
        )
        for item in items
    ]