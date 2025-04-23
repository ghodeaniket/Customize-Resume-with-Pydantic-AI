#!/usr/bin/env python3
"""
Test script for the health check endpoint.

This script creates a simplified FastAPI application that just includes
the health check endpoints for testing.
"""

import asyncio
import os
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse

# Create a stripped-down version of the API with just the health check
app = FastAPI(title="Resume Customizer Health Check")

@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Check if the API is up and running."
)
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0-test"
    }

@app.get(
    "/uploads-check",
    status_code=status.HTTP_200_OK,
    summary="Check uploads directory",
    description="Check if the uploads directory is accessible."
)
async def uploads_check():
    """Check if the uploads directory is accessible."""
    uploads_dir = "./uploads"
    
    try:
        # Ensure directory exists
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Try to write a test file
        test_file_path = os.path.join(uploads_dir, ".health_check_test")
        with open(test_file_path, "w") as f:
            f.write("test")
        
        # Clean up
        os.remove(test_file_path)
        
        return {
            "status": "ok",
            "message": "Uploads directory is accessible and writable"
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Error checking uploads directory: {str(e)}"
            }
        )

@app.get(
    "/",
    summary="Root endpoint",
    description="Welcome message for the API."
)
async def root():
    """Root endpoint."""
    return {
        "name": "Resume Customizer Health Check",
        "version": "0.1.0-test",
        "message": "Welcome to the Resume Customizer Health Check API",
    }

# Start the server when running this script directly
if __name__ == "__main__":
    print("=" * 80)
    print("STARTING HEALTH CHECK TEST SERVER")
    print("=" * 80)
    
    uvicorn.run(
        "test_health_check:app",
        host="127.0.0.1",
        port=9800,
        reload=False
    )
