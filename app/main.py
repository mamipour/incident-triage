from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import assist, ingest, search
from app.config import get_settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    app.include_router(ingest.router)
    app.include_router(search.router)
    app.include_router(assist.router)

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
