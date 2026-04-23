from typing import Dict

from fastapi import APIRouter

home_route = APIRouter()


@home_route.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}