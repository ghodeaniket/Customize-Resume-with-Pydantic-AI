"""Application entry point for the Resume Customizer.

This module initializes and configures the FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from resume_customizer import __version__
from resume_customizer.api.endpoints.health import router as health_router
from resume_customizer.api.endpoints.metrics import router as metrics_router
from resume_customizer.api.endpoints.resumes import router as resumes_router
from resume_customizer.api.endpoints.tasks import router as tasks_router
from resume_customizer.api.middleware import add_middleware
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import ResumeCustomizerException
from resume_customizer.core.logging import app_logger as logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.
    
    This function handles startup and shutdown events for the application.
    
    Args:
        app: The FastAPI application
    """
    # Startup
    logger.info(f"Starting Resume Customizer API v{__version__}")
    
    # Store API key in app state
    app.state.openrouter_api_key = settings.OPENROUTER_API_KEY
    
    # Yield control to the application
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Customizer API")


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    # Resume Customizer API
    
    This API provides services for analyzing and customizing resumes based on job descriptions.
    
    ## Features
    
    * **Resume Analysis**: Extract professional profiles from resumes
    * **Job Analysis**: Extract requirements from job descriptions
    * **Resume Customization**: Optimize resumes for specific job descriptions
    * **Multi-format Processing**: Support for PDF, DOCX, and TXT files
    * **Background Processing**: Handle large files asynchronously
    * **Performance Monitoring**: Track API usage and performance
    
    ## Authentication
    
    All endpoints require an API key in the `X-API-Key` header.
    
    ## File Upload
    
    File uploads are limited to {max_upload}MB and must be PDF, DOCX, or TXT format.
    """.format(max_upload=settings.MAX_UPLOAD_SIZE/1024/1024),
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}  # Hide schemas section by default
)


# Configure logging
setup_logging()


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
add_middleware(app)


# Exception handler
@app.exception_handler(ResumeCustomizerException)
async def resume_customizer_exception_handler(request: Request, exc: ResumeCustomizerException):
    """Handle custom exceptions.
    
    Args:
        request: The incoming request
        exc: The exception that was raised
        
    Returns:
        A JSON response with the error details
    """
    logger.error(f"ResumeCustomizerException: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"error": exc.message},
    )


# Include routers
app.include_router(resumes_router, prefix=settings.API_V1_PREFIX)
app.include_router(health_router)
app.include_router(metrics_router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint.
    
    Returns:
        A welcome message
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": __version__,
        "message": "Welcome to the Resume Customizer API",
    }


def main():
    """Entry point for the CLI."""
    from resume_customizer.cli import main as cli_main
    cli_main()

if __name__ == "__main__":
    main()
