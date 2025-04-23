"""Task endpoints for the Resume Customizer API.

This module provides endpoints for managing and monitoring background tasks.
"""

import os
import time
import uuid
from typing import Dict, List, Optional

import httpx
from fastapi import (
    APIRouter, 
    BackgroundTasks, 
    Depends, 
    File, 
    Form, 
    HTTPException, 
    Path, 
    Query, 
    UploadFile, 
    status
)
from loguru import logger
from pydantic import BaseModel, Field

from resume_customizer.api.dependencies import get_http_client, verify_api_key
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import (
    DocumentProcessingError,
    ValidationError
)
from resume_customizer.services.document import DocumentProcessor
from resume_customizer.services.tasks.processor import (
    process_resume_file,
    process_job_file,
    process_resume_customization,
    get_task_status,
    cleanup_tasks
)


# Task status response model
class TaskStatusResponse(BaseModel):
    """Response model for task status.
    
    Attributes:
        task_id: The task ID
        status: The task status
        progress: The task progress (0-100)
        file_path: The path to the processed file
        start_time: When the task started
        completion_time: When the task completed (if applicable)
        elapsed_time: Time elapsed since the task started
        result: The task result (if completed)
        error: The error message (if failed)
    """
    task_id: str = Field(..., description="The task ID")
    status: str = Field(..., description="The task status")
    progress: int = Field(..., description="The task progress (0-100)")
    file_path: str = Field(..., description="The path to the processed file")
    start_time: float = Field(..., description="When the task started")
    completion_time: Optional[float] = Field(None, description="When the task completed (if applicable)")
    elapsed_time: Optional[float] = Field(None, description="Time elapsed since the task started")
    result: Optional[Dict] = Field(None, description="The task result (if completed)")
    error: Optional[str] = Field(None, description="The error message (if failed)")


# Create router
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "/resume",
    response_model=Dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process a resume in the background",
    description="Upload and process a resume file in a background task."
)
async def process_resume_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="The resume file to process"),
    model_name: Optional[str] = Form(None, description="The model to use for analysis"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Process a resume file in the background.
    
    Args:
        background_tasks: The background tasks manager
        file: The resume file to process
        model_name: Optional override for the model name
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        Dict: The task ID and status URL
    """
    try:
        logger.info(f"Received request to process resume file in background: {file.filename}")
        
        # Validate file
        if not await DocumentProcessor.is_valid_file(file):
            raise ValidationError(
                f"Invalid file: {file.filename}. Must be PDF, DOCX, or TXT under "
                f"{settings.MAX_UPLOAD_SIZE/1024/1024:.1f}MB"
            )
        
        # Save the file
        file_path = await DocumentProcessor.save_file(file)
        
        # Generate a task ID
        task_id = str(uuid.uuid4())
        
        # Add the task to the background tasks
        background_tasks.add_task(
            process_resume_file,
            file_path=file_path,
            task_id=task_id,
            http_client=http_client,
            model_name=model_name
        )
        
        # Add a cleanup task
        background_tasks.add_task(
            cleanup_tasks,
            max_age_hours=24
        )
        
        # Return the task ID and status URL
        return {
            "task_id": task_id,
            "status_url": f"/api/v1/tasks/{task_id}",
            "file_path": str(file_path)
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/job",
    response_model=Dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process a job description in the background",
    description="Upload and process a job description file in a background task."
)
async def process_job_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="The job description file to process"),
    model_name: Optional[str] = Form(None, description="The model to use for analysis"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Process a job description file in the background.
    
    Args:
        background_tasks: The background tasks manager
        file: The job description file to process
        model_name: Optional override for the model name
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        Dict: The task ID and status URL
    """
    try:
        logger.info(f"Received request to process job file in background: {file.filename}")
        
        # Validate file
        if not await DocumentProcessor.is_valid_file(file):
            raise ValidationError(
                f"Invalid file: {file.filename}. Must be PDF, DOCX, or TXT under "
                f"{settings.MAX_UPLOAD_SIZE/1024/1024:.1f}MB"
            )
        
        # Save the file
        file_path = await DocumentProcessor.save_file(file)
        
        # Generate a task ID
        task_id = str(uuid.uuid4())
        
        # Add the task to the background tasks
        background_tasks.add_task(
            process_job_file,
            file_path=file_path,
            task_id=task_id,
            http_client=http_client,
            model_name=model_name
        )
        
        # Add a cleanup task
        background_tasks.add_task(
            cleanup_tasks,
            max_age_hours=24
        )
        
        # Return the task ID and status URL
        return {
            "task_id": task_id,
            "status_url": f"/api/v1/tasks/{task_id}",
            "file_path": str(file_path)
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/customize",
    response_model=Dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Customize a resume in the background",
    description="Upload a resume and customize it for a job description in a background task."
)
async def customize_resume_task(
    background_tasks: BackgroundTasks,
    resume_file: UploadFile = File(..., description="The resume file to customize"),
    job_description: str = Form(..., description="The job description content"),
    model_name: Optional[str] = Form(None, description="The model to use for customization"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Customize a resume for a job description in the background.
    
    Args:
        background_tasks: The background tasks manager
        resume_file: The resume file to customize
        job_description: The job description content
        model_name: Optional override for the model name
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        Dict: The task ID and status URL
    """
    try:
        logger.info(f"Received request to customize resume in background: {resume_file.filename}")
        
        # Validate file
        if not await DocumentProcessor.is_valid_file(resume_file):
            raise ValidationError(
                f"Invalid file: {resume_file.filename}. Must be PDF, DOCX, or TXT under "
                f"{settings.MAX_UPLOAD_SIZE/1024/1024:.1f}MB"
            )
        
        # Save the file
        file_path = await DocumentProcessor.save_file(resume_file)
        
        # Generate a task ID
        task_id = str(uuid.uuid4())
        
        # Add the task to the background tasks
        background_tasks.add_task(
            process_resume_customization,
            resume_file_path=file_path,
            job_description=job_description,
            task_id=task_id,
            http_client=http_client,
            model_name=model_name
        )
        
        # Add a cleanup task
        background_tasks.add_task(
            cleanup_tasks,
            max_age_hours=24
        )
        
        # Return the task ID and status URL
        return {
            "task_id": task_id,
            "status_url": f"/api/v1/tasks/{task_id}",
            "file_path": str(file_path)
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get task status",
    description="Get the status of a background task."
)
async def task_status(
    task_id: str = Path(..., description="The task ID")
):
    """Get the status of a background task.
    
    Args:
        task_id: The task ID
        
    Returns:
        TaskStatusResponse: The task status
    """
    try:
        # Get the task status
        status_data = await get_task_status(task_id)
        
        if status_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        # Calculate elapsed time if not completed
        if status_data.get("elapsed_time") is None:
            status_data["elapsed_time"] = time.time() - status_data["start_time"]
        
        # Convert to response model
        return TaskStatusResponse(
            task_id=task_id,
            **status_data
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Error getting task status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting task status: {str(e)}"
        )


@router.get(
    "",
    response_model=List[str],
    summary="List all tasks",
    description="Get a list of all task IDs."
)
async def list_tasks(
    api_key: str = Depends(verify_api_key),
    status: Optional[str] = Query(None, description="Filter by task status")
):
    """Get a list of all task IDs.
    
    Args:
        api_key: The API key for authentication
        status: Optional filter by task status
        
    Returns:
        List[str]: List of task IDs
    """
    try:
        from resume_customizer.services.tasks.processor import task_status as task_status_dict
        
        if status:
            # Filter by status
            task_ids = [
                task_id for task_id, task_data in task_status_dict.items()
                if task_data.get("status") == status
            ]
        else:
            # Return all tasks
            task_ids = list(task_status_dict.keys())
        
        return task_ids
        
    except Exception as e:
        logger.exception(f"Error listing tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tasks: {str(e)}"
        )
