"""API package."""
from fastapi import APIRouter, Depends

from api.dependencies import get_settings, get_uptime
from api.endpoints import resumes
from core.config import Settings


# Create main API router
router = APIRouter()

# Include endpoint routers
router.include_router(resumes.router)


@router.get(
    "/health",
    tags=["health"],
    summary="Health check endpoint",
    description="Check if the API is running properly"
)
async def health_check(
    settings: Settings = Depends(get_settings),
    uptime: float = Depends(get_uptime)
):
    """Health check endpoint.
    
    Args:
        settings: Application settings
        uptime: Application uptime
        
    Returns:
        dict: Health check response with system status
    """
    import platform
    import psutil
    
    # Get system information
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "ok",
        "api": {
            "version": settings.api_version,
            "title": settings.api_title,
            "uptime_seconds": uptime
        },
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
            "memory_total_mb": memory.total / (1024 * 1024),
            "memory_available_mb": memory.available / (1024 * 1024),
            "memory_used_percent": memory.percent,
            "disk_total_gb": disk.total / (1024 * 1024 * 1024),
            "disk_free_gb": disk.free / (1024 * 1024 * 1024),
            "disk_used_percent": disk.percent
        },
        "config": settings.dict_with_environment_info()
    }
