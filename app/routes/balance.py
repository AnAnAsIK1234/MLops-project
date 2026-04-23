from fastapi import APIRouter, Depends

from api.dependencies import get_current_user, get_db
from api.schemas.balance import BalanceResponse, TopUpRequest, TransactionResponse
from database.models import UserORM
from database.services.balance_service import BalanceService

balance_router = APIRouter(prefix="/balance", tags=["Balance"])


@balance_router.get("/", response_model=BalanceResponse)
def get_balance(
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    service = BalanceService(db)
    balance = service.get_balance(current_user.id)
    return BalanceResponse(
        user_id=current_user.id,
        credits=balance.credits,
        updated_at=balance.updated_at,
    )


@balance_router.post("/top-up", response_model=BalanceResponse)
def top_up_balance(
    payload: TopUpRequest,
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    service = BalanceService(db)
    balance = service.top_up(
        user_id=current_user.id,
        amount=payload.amount,
        description=payload.description or "balance top up",
    )
    return BalanceResponse(
        user_id=current_user.id,
        credits=balance.credits,
        updated_at=balance.updated_at,
    )


@balance_router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    current_user: UserORM = Depends(get_current_user),
    db=Depends(get_db),
):
    service = BalanceService(db)
    items = service.get_transactions(current_user.id)
    return [
        TransactionResponse(
            id=item.id,
            amount=item.amount,
            transaction_type=item.transaction_type,
            description=item.description,
            created_at=item.created_at,
        )
        for item in items
    ]