from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from instructor.api.curriculum import router as curriculum_router
from instructor.api.learner import router as learner_router
from instructor.api.placement import router as placement_router
from instructor.api.session import router as session_router
from instructor.config import settings
from instructor.curriculum.registry import CurriculumRegistry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.registry = CurriculumRegistry(settings.curriculum_path)
    yield


app = FastAPI(
    title="Instructor",
    description="Greek and Latin language instruction system",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(learner_router)
app.include_router(session_router)
app.include_router(curriculum_router)
app.include_router(placement_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
