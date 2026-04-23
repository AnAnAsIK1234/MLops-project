from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_user, get_db
from api.schemas.history import HistoryItemResponse, PredictionEventResponse
from api.schemas.prediction import PredictionHistoryItem
from database.models import UserORM
from database.services.history_service import HistoryService
from database.services.prediction_service import PredictionService

history_router = APIRouter(prefix="/history", tags=["History"])


@history_router.get("/", response_model=list[HistoryItemResponse])
def all_history(
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    service = HistoryService(db)
    items = service.get_user_history(current_user.id)
    return [HistoryItemResponse(**item) for item in items]


@history_router.get("/predictions", response_model=list[PredictionHistoryItem])
def prediction_history(
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    service = PredictionService(db)
    items = service.user_prediction_history(current_user.id)
    return [PredictionHistoryItem(**item) for item in items]


@history_router.get("/predictions/{task_id}", response_model=list[PredictionEventResponse])
def prediction_events(
    task_id: str,
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    service = PredictionService(db)
    task = service.get_task(task_id)

    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    history = service.get_task_history(task_id)
    return [
        PredictionEventResponse(
            event_name=item.event_name,
            details_json=item.details_json,
            created_at=item.created_at.isoformat(),
        )
        for item in history
    ]