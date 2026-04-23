from api.fastapi_module import create_application
from database.db import Base, ENGINE, SessionLocal
from database.services.bootstrap_service import BootstrapService

app = create_application()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=ENGINE)
    with SessionLocal() as session:
        BootstrapService(session).seed_demo_data()
        session.commit()