from backend.app.api.health import router as health_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.resumes import router as resumes_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.candidates import router as candidates_router

__all__ = [
    "health_router",
    "jobs_router",
    "resumes_router",
    "evaluation_router",
    "candidates_router",
]
