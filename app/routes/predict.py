import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from api.dependencies import get_current_user, get_db
from api.schemas.prediction import (
    PredictAcceptedResponse,
    PredictFormRequest,
    PredictResultResponse,
    ValidationErrorItem,
)
from database.models import RequestSource, UserORM
from database.services.prediction_service import PredictionService
from database.services.validation_service import ValidationService
from src.rabbitmq import publish_message

predict_router = APIRouter(prefix="/predict", tags=["Predict"])


@predict_router.post("/form", response_model=PredictAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def predict_form(
    payload: PredictFormRequest,
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    validator = ValidationService()
    valid_records, invalid_records = validator.validate_form(payload.prompt)

    if not valid_records:
        raise ValueError("Prompt is empty")

    service = PredictionService(db)
    task = service.create_task(
        user_id=current_user.id,
        model_id=payload.model_id,
        valid_records=valid_records,
        invalid_records=invalid_records,
        request_source=RequestSource.FORM.value,
    )

    try:
        publish_message({"task_id": task.id})
    except Exception as exc:
        service.complete_task_failed(task.id, f"RabbitMQ publish error: {exc}")
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to publish task to queue") from exc

    return PredictAcceptedResponse(
        task_id=task.id,
        status=task.status,
        processed_count=len(valid_records),
        rejected_count=len(invalid_records),
        validation_errors=[],
    )


@predict_router.post("/file", response_model=PredictAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def predict_file(
    model_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    content = await file.read()

    validator = ValidationService()
    valid_records, invalid_records = validator.validate_csv_bytes(content)

    if not valid_records:
        raise ValueError("No valid prompts found in file")

    service = PredictionService(db)
    task = service.create_task(
        user_id=current_user.id,
        model_id=model_id,
        valid_records=valid_records,
        invalid_records=invalid_records,
        request_source=RequestSource.FILE.value,
        source_filename=file.filename,
    )

    try:
        publish_message({"task_id": task.id})
    except Exception as exc:
        service.complete_task_failed(task.id, f"RabbitMQ publish error: {exc}")
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to publish task to queue") from exc
    return PredictAcceptedResponse(
        task_id=task.id,
        status=task.status,
        processed_count=len(valid_records),
        rejected_count=len(invalid_records),
        validation_errors=[ValidationErrorItem(**item) for item in invalid_records],
    )


@predict_router.get("/{task_id}", response_model=PredictResultResponse)
def get_prediction_result(
    task_id: str,
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    service = PredictionService(db)
    task = service.get_task(task_id)

    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if task.result is None:
        return PredictResultResponse(
            task_id=task.id,
            status=task.status,
            charged_credits=task.charged_credits,
            processed_count=task.valid_records,
            rejected_count=task.invalid_records,
            result=[],
            summary={},
            error_message=task.error_message,
        )

    return PredictResultResponse(
        task_id=task.id,
        status=task.status,
        charged_credits=task.charged_credits,
        processed_count=task.valid_records,
        rejected_count=task.invalid_records,
        result=json.loads(task.result.output_json),
        summary=json.loads(task.result.summary_json),
        error_message=task.error_message,
    )