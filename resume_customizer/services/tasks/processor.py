"""Background tasks for processing files.

This module contains background tasks for processing files asynchronously.
"""

import os
import time
from pathlib import Path
from typing import Dict, Optional

import httpx
from fastapi import BackgroundTasks
from loguru import logger

from resume_customizer.agents.profiler import analyze_resume
from resume_customizer.agents.researcher import analyze_job_description
from resume_customizer.agents.strategist import customize_resume
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import DocumentProcessingError
from resume_customizer.services.document import DocumentProcessor


# Dictionary to track task status
task_status: Dict[str, Dict] = {}


async def process_resume_file(
    file_path: Path,
    task_id: str,
    http_client: httpx.AsyncClient,
    model_name: Optional[str] = None
) -> None:
    """Process a resume file in the background.
    
    Args:
        file_path: Path to the resume file
        task_id: Unique ID for this task
        http_client: HTTP client for making requests
        model_name: Optional override for the model name
    """
    logger.info(f"Starting background task {task_id} to process resume file: {file_path}")
    
    start_time = time.time()
    
    # Update task status
    task_status[task_id] = {
        "status": "processing",
        "file_path": str(file_path),
        "start_time": start_time,
        "progress": 0,
        "result": None,
        "error": None
    }
    
    try:
        # Extract text from the file
        task_status[task_id]["progress"] = 10
        task_status[task_id]["status"] = "extracting_text"
        
        text = await DocumentProcessor.extract_text(file_path)
        
        task_status[task_id]["progress"] = 40
        task_status[task_id]["status"] = "analyzing"
        
        # Analyze the resume
        profile = await analyze_resume(
            resume_content=text,
            http_client=http_client,
            model_name=model_name
        )
        
        # Update task status
        task_status[task_id]["progress"] = 100
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["result"] = profile.dict()
        task_status[task_id]["completion_time"] = time.time()
        task_status[task_id]["elapsed_time"] = time.time() - start_time
        
        logger.info(f"Completed background task {task_id} in {time.time() - start_time:.2f}s")
        
    except Exception as e:
        logger.exception(f"Error in background task {task_id}: {str(e)}")
        
        # Update task status
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["completion_time"] = time.time()
        task_status[task_id]["elapsed_time"] = time.time() - start_time


async def process_job_file(
    file_path: Path,
    task_id: str,
    http_client: httpx.AsyncClient,
    model_name: Optional[str] = None
) -> None:
    """Process a job description file in the background.
    
    Args:
        file_path: Path to the job description file
        task_id: Unique ID for this task
        http_client: HTTP client for making requests
        model_name: Optional override for the model name
    """
    logger.info(f"Starting background task {task_id} to process job file: {file_path}")
    
    start_time = time.time()
    
    # Update task status
    task_status[task_id] = {
        "status": "processing",
        "file_path": str(file_path),
        "start_time": start_time,
        "progress": 0,
        "result": None,
        "error": None
    }
    
    try:
        # Extract text from the file
        task_status[task_id]["progress"] = 10
        task_status[task_id]["status"] = "extracting_text"
        
        text = await DocumentProcessor.extract_text(file_path)
        
        task_status[task_id]["progress"] = 40
        task_status[task_id]["status"] = "analyzing"
        
        # Analyze the job description
        requirements = await analyze_job_description(
            job_description=text,
            http_client=http_client,
            model_name=model_name
        )
        
        # Update task status
        task_status[task_id]["progress"] = 100
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["result"] = requirements.dict()
        task_status[task_id]["completion_time"] = time.time()
        task_status[task_id]["elapsed_time"] = time.time() - start_time
        
        logger.info(f"Completed background task {task_id} in {time.time() - start_time:.2f}s")
        
    except Exception as e:
        logger.exception(f"Error in background task {task_id}: {str(e)}")
        
        # Update task status
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["completion_time"] = time.time()
        task_status[task_id]["elapsed_time"] = time.time() - start_time


async def process_resume_customization(
    resume_file_path: Path,
    job_description: str,
    task_id: str,
    http_client: httpx.AsyncClient,
    model_name: Optional[str] = None
) -> None:
    """Process a resume customization in the background.
    
    Args:
        resume_file_path: Path to the resume file
        job_description: The job description content
        task_id: Unique ID for this task
        http_client: HTTP client for making requests
        model_name: Optional override for the model name
    """
    logger.info(f"Starting background task {task_id} to customize resume: {resume_file_path}")
    
    start_time = time.time()
    
    # Update task status
    task_status[task_id] = {
        "status": "processing",
        "file_path": str(resume_file_path),
        "start_time": start_time,
        "progress": 0,
        "result": None,
        "error": None
    }
    
    try:
        # Extract text from the resume file
        task_status[task_id]["progress"] = 10
        task_status[task_id]["status"] = "extracting_resume"
        
        resume_text = await DocumentProcessor.extract_text(resume_file_path)
        
        task_status[task_id]["progress"] = 30
        task_status[task_id]["status"] = "customizing"
        
        # Customize the resume
        optimized_resume = await customize_resume(
            resume_content=resume_text,
            job_description=job_description,
            http_client=http_client,
            model_name=model_name
        )
        
        # Update task status
        task_status[task_id]["progress"] = 100
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["result"] = optimized_resume.dict()
        task_status[task_id]["completion_time"] = time.time()
        task_status[task_id]["elapsed_time"] = time.time() - start_time
        
        logger.info(f"Completed background task {task_id} in {time.time() - start_time:.2f}s")
        
    except Exception as e:
        logger.exception(f"Error in background task {task_id}: {str(e)}")
        
        # Update task status
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["error"] = str(e)
        task_status[task_id]["completion_time"] = time.time()
        task_status[task_id]["elapsed_time"] = time.time() - start_time


async def get_task_status(task_id: str) -> Optional[Dict]:
    """Get the status of a background task.
    
    Args:
        task_id: The task ID
        
    Returns:
        Dict: The task status, or None if not found
    """
    return task_status.get(task_id)


async def cleanup_tasks(max_age_hours: int = 24) -> None:
    """Clean up old tasks from the status dictionary.
    
    Args:
        max_age_hours: Maximum age in hours before a task is removed
    """
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    # Find tasks to remove
    tasks_to_remove = []
    for task_id, status in task_status.items():
        if status.get("completion_time") and (current_time - status["completion_time"]) > max_age_seconds:
            tasks_to_remove.append(task_id)
    
    # Remove the tasks
    for task_id in tasks_to_remove:
        del task_status[task_id]
    
    if tasks_to_remove:
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
