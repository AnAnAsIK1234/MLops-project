from typing import Dict
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

home_route = APIRouter()


@home_route.get(
    "/",
    response_model=Dict[str, str],
    summary="Root endpoint",
    description="Returns a welcome message"
)
async def index() -> Dict[str, str]:
    """
    Root endpoing returning welcome message

    Returns:
        Dict[str, str]: Welcome message
    """
    try:
        return {"message": "Welcome to Event Planner API!!!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="internal server error")



@home_route.get(
    "/health",
    response_model=Dict[str, str],
    summary="Health check endpoint",
    description="Returns service health status"
)
async def health_check() -> Dict[str, str]:
    try:
        return {"message": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="server not ok :(")