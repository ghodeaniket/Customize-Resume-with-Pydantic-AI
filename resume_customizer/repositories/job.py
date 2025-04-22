"""Job repository for the Resume Customizer application.

This module defines the repository for job data operations.
"""

from typing import List, Optional
import uuid

from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.core.logging import app_logger as logger
from resume_customizer.repositories.base import BaseRepository


class JobRepository(BaseRepository[JobRequirements]):
    """Repository for job data operations.
    
    This class handles storage and retrieval of job requirements. For Phase 1,
    this will use in-memory storage. In future phases, we can extend this
    to use a database.
    """
    
    def __init__(self):
        """Initialize the job repository."""
        super().__init__(JobRequirements)
    
    async def create_with_generated_id(self, job: JobRequirements) -> tuple[str, JobRequirements]:
        """Create a job with a generated ID.
        
        Args:
            job: The job to create
            
        Returns:
            tuple: The generated ID and the created job
        """
        # Generate a unique ID
        job_id = str(uuid.uuid4())
        
        # Store the job
        await self.create(job_id, job)
        
        logger.info(f"Created job with generated ID: {job_id}")
        return job_id, job
    
    async def get_by_keyword(self, keyword: str) -> List[JobRequirements]:
        """Get jobs that contain a keyword.
        
        Args:
            keyword: The keyword to search for
            
        Returns:
            List[JobRequirements]: The matching jobs
        """
        logger.debug(f"Searching jobs for keyword: {keyword}")
        
        # Filter jobs by keyword in keywords list (case-insensitive)
        keyword_lower = keyword.lower()
        
        results = [
            job for job in self._items.values()
            if any(keyword_lower in kw.lower() for kw in job.keywords)
        ]
        
        logger.debug(f"Found {len(results)} jobs matching keyword: {keyword}")
        return results
    
    async def get_by_position_title(self, title: str) -> List[JobRequirements]:
        """Get jobs by position title.
        
        Args:
            title: The position title to search for
            
        Returns:
            List[JobRequirements]: The matching jobs
        """
        logger.debug(f"Searching jobs for position title: {title}")
        
        # Filter jobs by position title (case-insensitive)
        title_lower = title.lower()
        
        results = [
            job for job in self._items.values()
            if title_lower in job.position.title.lower()
        ]
        
        logger.debug(f"Found {len(results)} jobs matching position title: {title}")
        return results


# Instantiate the repository
job_repository = JobRepository()
