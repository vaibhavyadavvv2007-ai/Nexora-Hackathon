from fastapi import FastAPI
from backend.app.api.health import router as health_router
from backend.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Deterministic and explainable candidate shortlisting engine.",
    version="0.1.0",
    debug=settings.DEBUG
)

# Register health check router directly at root for GET /health
app.include_router(health_router)
