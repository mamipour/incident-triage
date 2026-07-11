from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import assist, incidents, ingest, search
from app.config import get_settings
from app.db import init_db
from app.observability import CorrelationIdMiddleware, configure_logging, router as debug_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Incident Triage",
        description="Search and AI assistant for incident triage",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(CorrelationIdMiddleware)

    app.include_router(ingest.router)
    app.include_router(search.router)
    app.include_router(incidents.router)
    app.include_router(assist.router)
    app.include_router(debug_router)

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    app.state.settings = settings
    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
