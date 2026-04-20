from typing import Dict
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

home_route = APIRouter()


@home_route.get(
    "/signup",
    response_model=Dict[str, str],
    summary="User Registration",
    description="Registration a new user with email and password"
)
async def index() -> Dict[str, str]:
    ...
