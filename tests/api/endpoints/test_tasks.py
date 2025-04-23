"""Tests for the task endpoints.

This module contains tests for the task API endpoints.
"""

import io
import json
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from resume_customizer.api.endpoints.tasks import router
from resume_customizer.core.exceptions import DocumentProcessingError, ValidationError


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router)
    
    # Mock dependencies
    app.dependency_overrides = {}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return TestClient(app)


@pytest.fixture
def mock_document_processor():
    """Mock the DocumentProcessor class."""
    with patch('resume_customizer.api.endpoints.tasks.DocumentProcessor') as mock:
        # Set up mock methods
        mock.is_valid_file = AsyncMock(return_value=True)
        mock.save_file = AsyncMock(return_value="uploads/test_resume.pdf")
        mock.extract_text = AsyncMock(return_value="Sample resume content")
        yield mock


@pytest.fixture
def mock_process_function():
    """Mock the process functions."""
    with patch('resume_customizer.api.endpoints.tasks.process_resume_file', new_callable=AsyncMock) as mock_resume, \
         patch('resume_customizer.api.endpoints.tasks.process_job_file', new_callable=AsyncMock) as mock_job, \
         patch('resume_customizer.api.endpoints.tasks.process_resume_customization', new_callable=AsyncMock) as mock_customize, \
         patch('resume_customizer.api.endpoints.tasks.cleanup_tasks', new_callable=AsyncMock) as mock_cleanup:
        
        yield {
            "resume": mock_resume,
            "job": mock_job,
            "customize": mock_customize,
            "cleanup": mock_cleanup
        }


@pytest.fixture
def mock_task_status():
    """Mock the task status functions."""
    task_id = str(uuid.uuid4())
    status_data = {
        "status": "processing",
        "file_path": "uploads/test_resume.pdf",
        "start_time": time.time(),
        "progress": 50,
        "result": None,
        "error": None
    }
    
    with patch('resume_customizer.api.endpoints.tasks.get_task_status', new_callable=AsyncMock) as mock_get_status:
        mock_get_status.return_value = status_data
        
        with patch('resume_customizer.services.tasks.processor.task_status', {task_id: status_data}):
            yield mock_get_status, task_id, status_data


@pytest.fixture
def sample_file():
    """Create a sample file for testing."""
    content = b"Sample content"
    return io.BytesIO(content)


class TestTaskEndpoints:
    """Test cases for the task API endpoints."""
    
    @pytest.mark.asyncio
    async def test_process_resume_task(self, app, mock_document_processor, mock_process_function, sample_file):
        """Test the process resume task endpoint."""
        # Setup file upload
        file = {"file": ("test_resume.pdf", sample_file, "application/pdf")}
        form_data = {"model_name": "test-model"}
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/tasks/resume", files=file, data=form_data)
        
        # Verify response
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert "status_url" in data
        assert "file_path" in data
        
        # Verify mocks were called
        mock_document_processor.is_valid_file.assert_called_once()
        mock_document_processor.save_file.assert_called_once()
        mock_process_function["resume"].assert_called_once()
        mock_process_function["cleanup"].assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_job_task(self, app, mock_document_processor, mock_process_function, sample_file):
        """Test the process job task endpoint."""
        # Setup file upload
        file = {"file": ("test_job.pdf", sample_file, "application/pdf")}
        form_data = {"model_name": "test-model"}
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/tasks/job", files=file, data=form_data)
        
        # Verify response
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert "status_url" in data
        assert "file_path" in data
        
        # Verify mocks were called
        mock_document_processor.is_valid_file.assert_called_once()
        mock_document_processor.save_file.assert_called_once()
        mock_process_function["job"].assert_called_once()
        mock_process_function["cleanup"].assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customize_resume_task(self, app, mock_document_processor, mock_process_function, sample_file):
        """Test the customize resume task endpoint."""
        # Setup file upload
        file = {"resume_file": ("test_resume.pdf", sample_file, "application/pdf")}
        form_data = {
            "job_description": "Sample job description",
            "model_name": "test-model"
        }
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/tasks/customize", files=file, data=form_data)
        
        # Verify response
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        assert "status_url" in data
        assert "file_path" in data
        
        # Verify mocks were called
        mock_document_processor.is_valid_file.assert_called_once()
        mock_document_processor.save_file.assert_called_once()
        mock_process_function["customize"].assert_called_once()
        mock_process_function["cleanup"].assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_status(self, app, mock_task_status):
        """Test the task status endpoint."""
        mock_get_status, task_id, status_data = mock_task_status
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(f"/tasks/{task_id}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == status_data["status"]
        assert data["progress"] == status_data["progress"]
        assert data["file_path"] == status_data["file_path"]
        
        # Verify mock was called
        mock_get_status.assert_called_once_with(task_id)
    
    @pytest.mark.asyncio
    async def test_task_status_not_found(self, app):
        """Test the task status endpoint with a nonexistent task."""
        # Mock get_task_status to return None
        with patch('resume_customizer.api.endpoints.tasks.get_task_status', new_callable=AsyncMock) as mock_get_status:
            mock_get_status.return_value = None
            
            # Send request using AsyncClient
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.get("/tasks/nonexistent")
            
            # Verify response
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
            
            # Verify mock was called
            mock_get_status.assert_called_once_with("nonexistent")
    
    @pytest.mark.asyncio
    async def test_list_tasks(self, app, mock_task_status):
        """Test the list tasks endpoint."""
        mock_get_status, task_id, status_data = mock_task_status
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/tasks")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert task_id in data
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(self, app, mock_task_status):
        """Test the list tasks endpoint with a status filter."""
        mock_get_status, task_id, status_data = mock_task_status
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/tasks?status=processing")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert task_id in data
        
        # Send request with a different status
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/tasks?status=completed")
        
        # Verify no tasks are returned
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_validation_error(self, app, mock_document_processor, sample_file):
        """Test error handling for validation errors."""
        # Setup mock to indicate an invalid file
        mock_document_processor.is_valid_file.return_value = False
        
        # Setup file upload
        file = {"file": ("test_resume.pdf", sample_file, "application/pdf")}
        form_data = {"model_name": "test-model"}
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/tasks/resume", files=file, data=form_data)
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "Invalid file" in data["detail"]
