from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Schema for health endpoint response."""
    status: str = "ok"
