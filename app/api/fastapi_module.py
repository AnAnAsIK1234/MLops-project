from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.exception_handlers import register_exception_handlers
from config import settings
from routes.auth import auth_router
from routes.balance import balance_router
from routes.history import history_router
from routes.home import home_route
from routes.models import models_router
from routes.pages import pages_router
from routes.predict import predict_router


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory="static"), name="static")

    register_exception_handlers(app)

    app.include_router(home_route, tags=["Home"])
    app.include_router(pages_router)
    app.include_router(auth_router)
    app.include_router(balance_router)
    app.include_router(models_router)
    app.include_router(predict_router)
    app.include_router(history_router)

    return app