from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.candidates import router as candidates_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.health import router as health_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.resumes import router as resumes_router
from backend.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Deterministic and explainable candidate shortlisting engine.",
    version="0.1.0",
    debug=settings.DEBUG,
)

# CORS middleware with explicit development and production frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register health check router directly at root for GET /health
app.include_router(health_router)

# Register domain API routers matching frontend endpoints
app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(evaluation_router)
app.include_router(candidates_router)
