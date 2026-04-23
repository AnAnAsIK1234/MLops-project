from typing import Dict

from fastapi import APIRouter

home_route = APIRouter()


@home_route.get("/", response_model=Dict[str, str])
async def index() -> Dict[str, str]:
    return {"message": "Welcome to ML prediction service"}


@home_route.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    return {"message": "ok"}
