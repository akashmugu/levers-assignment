from fastapi import FastAPI

from app.routes import router as bills_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Billing Service",
        description="A minimal billing microservice",
        version="1.0.0",
    )
    app.include_router(bills_router)
    return app


app = create_app()
