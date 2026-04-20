from fastapi import APIRouter, Depends

from api.dependencies import get_current_user, get_db
from api.schemas.prediction import PredictRequest, PredictResponse
from database.models import UserORM
from database.services.model_service import ModelService
from database.services.prediction_service import PredictionService

predict_router = APIRouter(prefix="/predict", tags=["Predict"])


@predict_router.post("/", response_model=PredictResponse)
def predict(
    payload: PredictRequest,
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    prediction_service = PredictionService(db)
    model_service = ModelService(db)

    model = model_service.get_enabled_model(payload.model_id)
    task = prediction_service.create_task(
        user_id=current_user.id,
        model_id=payload.model_id,
        input_data=payload.input_data,
    )
    result = prediction_service.run_task(task.id)

    return PredictResponse(
        task_id=task.id,
        status="success",
        output_ref=result.output_ref,
        latency_ms=result.latency_ms,
        charged_credits=model.price_per_request,
    )