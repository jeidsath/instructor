import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from instructor.api.curriculum import router as curriculum_router
from instructor.api.learner import router as learner_router
from instructor.api.placement import router as placement_router
from instructor.api.session import router as session_router
from instructor.config import settings
from instructor.curriculum.registry import CurriculumRegistry
from instructor.log_config import configure_logging

logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status, and duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level)
    logger.info("Starting Instructor application")
    app.state.registry = CurriculumRegistry(settings.curriculum_path)
    logger.info("Curriculum registry loaded")
    yield
    logger.info("Shutting down Instructor application")


app = FastAPI(
    title="Instructor",
    description="Greek and Latin language instruction system",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(learner_router)
app.include_router(session_router)
app.include_router(curriculum_router)
app.include_router(placement_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Production static file serving: serve built frontend if dist/ exists
if FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    index_html = FRONTEND_DIST / "index.html"

    @app.get("/{path:path}")
    async def serve_spa(path: str) -> Response:
        """Serve index.html for all non-API routes (SPA catch-all)."""
        return FileResponse(str(index_html))
