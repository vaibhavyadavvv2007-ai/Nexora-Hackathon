from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.candidates import router as candidates_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.health import router as health_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.resumes import router as resumes_router
from backend.app.store import get_store
from backend.config.settings import get_settings
from backend.core.pipeline import get_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-load official Sample JD if available and no job stored
    try:
        sample_jd_path = Path("data/official/Sample_JD.pdf")
        if sample_jd_path.exists():
            store = get_store()
            if not store.get_job():
                pipeline = get_pipeline()
                content = sample_jd_path.read_bytes()
                jd = pipeline.parse_job_description(source=content, doc_id="official_sample_jd")
                jd.source_file = "Sample_JD.pdf"
                store.save_job(jd)
    except Exception as exc:
        print(f"Warning: Could not pre-load sample JD: {exc}")
    yield


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Deterministic and explainable candidate shortlisting engine.",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
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
