"""Resume repository for the Resume Customizer application.

This module defines the repository for resume data operations.
"""

from typing import List, Optional
import uuid

from resume_customizer.agents.models.resume import OptimizedResume
from resume_customizer.core.logging import app_logger as logger
from resume_customizer.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[OptimizedResume]):
    """Repository for resume data operations.
    
    This class handles storage and retrieval of optimized resumes. For Phase 1,
    this will use in-memory storage. In future phases, we can extend this
    to use a database.
    """
    
    def __init__(self):
        """Initialize the resume repository."""
        super().__init__(OptimizedResume)
    
    async def create_with_generated_id(self, resume: OptimizedResume) -> tuple[str, OptimizedResume]:
        """Create a resume with a generated ID.
        
        Args:
            resume: The resume to create
            
        Returns:
            tuple: The generated ID and the created resume
        """
        # Generate a unique ID
        resume_id = str(uuid.uuid4())
        
        # Store the resume
        await self.create(resume_id, resume)
        
        logger.info(f"Created resume with generated ID: {resume_id}")
        return resume_id, resume
    
    async def get_by_keyword(self, keyword: str) -> List[OptimizedResume]:
        """Get resumes that contain a keyword.
        
        Args:
            keyword: The keyword to search for
            
        Returns:
            List[OptimizedResume]: The matching resumes
        """
        logger.debug(f"Searching resumes for keyword: {keyword}")
        
        # Filter resumes by keyword (case-insensitive)
        keyword_lower = keyword.lower()
        
        results = [
            resume for resume in self._items.values()
            if keyword_lower in resume.content.lower()
        ]
        
        logger.debug(f"Found {len(results)} resumes matching keyword: {keyword}")
        return results


# Instantiate the repository
resume_repository = ResumeRepository()
