from fastapi import FastAPI

from instructor.api.curriculum import router as curriculum_router
from instructor.api.learner import router as learner_router
from instructor.api.placement import router as placement_router
from instructor.api.session import router as session_router

app = FastAPI(
    title="Instructor",
    description="Greek and Latin language instruction system",
    version="0.1.0",
)

app.include_router(learner_router)
app.include_router(session_router)
app.include_router(curriculum_router)
app.include_router(placement_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
