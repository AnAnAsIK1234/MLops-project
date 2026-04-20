from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

<<<<<<< HEAD
from config import settings
from api.exception_handlers import register_exception_handlers
from routes.home import home_route
from routes.auth import auth_router
from routes.users import users_router
from routes.balance import balance_router
from routes.predict import predict_router
from routes.history import history_router

=======
from routes.home import home_route
from config import settings
>>>>>>> origin/hw3

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
<<<<<<< HEAD
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
=======
        version="1",
        docs_url="/api/docs/",
        redoc_url="/api/redoc"
    )

    # configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
>>>>>>> origin/hw3
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

<<<<<<< HEAD
    register_exception_handlers(app)

    app.include_router(home_route, tags=["Home"])
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(balance_router)
    app.include_router(predict_router)
    app.include_router(history_router)
=======
    app.include_router(home_route, tags=['Home'])
>>>>>>> origin/hw3

    return app