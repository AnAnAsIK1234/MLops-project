from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.home import home_route
from config import settings

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1",
        docs_url="/api/docs/",
        redoc_url="/api/redoc"
    )

    # configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(home_route, tags=['Home'])

    return app