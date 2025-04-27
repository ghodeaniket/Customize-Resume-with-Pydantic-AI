"""Main application module."""
import logging
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from api import router as api_router
from core.config import get_settings
from core.exceptions import ResumeCustomizerError
from core.logging import configure_logging


# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
from api.middleware import RateLimitMiddleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute if hasattr(settings, 'rate_limit_per_minute') else 60
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API router
app.include_router(api_router)


@app.exception_handler(ResumeCustomizerError)
async def resume_customizer_exception_handler(
    request: Request, exc: ResumeCustomizerError
) -> JSONResponse:
    """Handle ResumeCustomizerError exceptions.
    
    Args:
        request: Request instance
        exc: Exception instance
        
    Returns:
        JSONResponse: JSON response with error details
    """
    logger.error(f"ResumeCustomizerError: {exc.message}", extra={"details": exc.details})
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle RequestValidationError exceptions.
    
    Args:
        request: Request instance
        exc: Exception instance
        
    Returns:
        JSONResponse: JSON response with error details
    """
    logger.error(f"ValidationError: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation error",
            "details": {"errors": exc.errors()}
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle generic exceptions.
    
    Args:
        request: Request instance
        exc: Exception instance
        
    Returns:
        JSONResponse: JSON response with error details
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "details": {"error": str(exc)}
        }
    )


@app.on_event("startup")
async def startup_event() -> None:
    """Run startup tasks."""
    logger.info(f"Starting Resume Customizer API v{settings.api_version}")
    
    # Set environment variables for Pydantic AI + OpenRouter integration
    import os
    if settings.openrouter_api_key:
        logger.info("Setting OpenRouter API key for Pydantic AI")
        os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    else:
        logger.warning("No OpenRouter API key found in settings")
    
    # Initialize prompt manager and templates
    from infrastructure.init_prompts import init_prompt_manager
    logger.info("Initializing prompt templates")
    init_prompt_manager()
    logger.info("Prompt templates initialized successfully")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Run shutdown tasks."""
    logger.info("Shutting down Resume Customizer API")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting server with uvicorn")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
