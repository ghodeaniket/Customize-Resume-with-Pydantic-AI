"""API package."""
from fastapi import APIRouter, Depends

from api.dependencies import get_settings, get_uptime
from api.endpoints import resumes
from api.responses import HealthCheckResponse
from core.config import Settings


# Create main API router
router = APIRouter()

# Include endpoint routers
router.include_router(resumes.router)


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["health"],
    summary="Health check endpoint",
    description="Check if the API is running properly"
)
async def health_check(
    settings: Settings = Depends(get_settings),
    uptime: float = Depends(get_uptime)
) -> HealthCheckResponse:
    """Health check endpoint.
    
    Args:
        settings: Application settings
        uptime: Application uptime
        
    Returns:
        HealthCheckResponse: Health check response
    """
    return HealthCheckResponse(
        status="ok",
        version=settings.api_version,
        uptime=uptime
    )
