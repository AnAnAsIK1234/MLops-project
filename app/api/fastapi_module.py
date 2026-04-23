from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.exception_handlers import register_exception_handlers
from routes.home import home_route
from routes.auth import auth_router
from routes.users import users_router
from routes.balance import balance_router
from routes.predict import predict_router
from routes.history import history_router


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(home_route, tags=["Home"])
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(balance_router)
    app.include_router(predict_router)
    app.include_router(history_router)

    return app