"""Resume customization service.

This module contains the business logic for resume customization.
"""

from typing import Optional, Tuple

import httpx

from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.resume import OptimizedResume
from resume_customizer.agents.profiler import analyze_resume
from resume_customizer.agents.researcher import analyze_job_description
from resume_customizer.agents.strategist import customize_resume
from resume_customizer.core.exceptions import ResumeCustomizerException
from resume_customizer.core.logging import app_logger as logger


class CustomizerService:
    """Service for resume customization.
    
    This service orchestrates the resume customization process, delegating to
    the appropriate agents for each step.
    """
    
    async def analyze_resume(
        self,
        resume_content: str,
        http_client: httpx.AsyncClient,
        model_name: Optional[str] = None
    ) -> ProfessionalProfile:
        """Analyze a resume and create a professional profile.
        
        Args:
            resume_content: The resume content
            http_client: The HTTP client for making requests
            model_name: Optional override for the model name
            
        Returns:
            ProfessionalProfile: The extracted professional profile
            
        Raises:
            ResumeCustomizerException: If there's an error in the process
        """
        try:
            logger.info("Service: Starting resume analysis")
            
            profile = await analyze_resume(
                resume_content=resume_content,
                http_client=http_client,
                model_name=model_name
            )
            
            logger.info("Service: Resume analysis completed")
            return profile
        
        except Exception as e:
            error_msg = f"Resume analysis failed in service: {str(e)}"
            logger.error(error_msg)
            raise ResumeCustomizerException(error_msg)
    
    async def analyze_job(
        self,
        job_description: str,
        http_client: httpx.AsyncClient,
        model_name: Optional[str] = None
    ) -> JobRequirements:
        """Analyze a job description and extract requirements.
        
        Args:
            job_description: The job description content
            http_client: The HTTP client for making requests
            model_name: Optional override for the model name
            
        Returns:
            JobRequirements: The extracted job requirements
            
        Raises:
            ResumeCustomizerException: If there's an error in the process
        """
        try:
            logger.info("Service: Starting job description analysis")
            
            requirements = await analyze_job_description(
                job_description=job_description,
                http_client=http_client,
                model_name=model_name
            )
            
            logger.info("Service: Job description analysis completed")
            return requirements
        
        except Exception as e:
            error_msg = f"Job analysis failed in service: {str(e)}"
            logger.error(error_msg)
            raise ResumeCustomizerException(error_msg)
    
    async def customize(
        self,
        resume_content: str,
        job_description: str,
        http_client: httpx.AsyncClient,
        model_name: Optional[str] = None,
        include_analysis: bool = False
    ) -> Tuple[OptimizedResume, Optional[ProfessionalProfile], Optional[JobRequirements]]:
        """Customize a resume for a specific job.
        
        Args:
            resume_content: The resume content
            job_description: The job description content
            http_client: The HTTP client for making requests
            model_name: Optional override for the model name
            include_analysis: Whether to include full analysis in the response
            
        Returns:
            A tuple containing:
                - OptimizedResume: The optimized resume
                - Optional[ProfessionalProfile]: The professional profile (if requested)
                - Optional[JobRequirements]: The job requirements (if requested)
            
        Raises:
            ResumeCustomizerException: If there's an error in the process
        """
        try:
            logger.info("Service: Starting resume customization")
            
            # Customize the resume
            optimized_resume = await customize_resume(
                resume_content=resume_content,
                job_description=job_description,
                http_client=http_client,
                model_name=model_name
            )
            
            profile = None
            requirements = None
            
            # If requested, include the analysis
            if include_analysis:
                logger.info("Service: Including full analysis in response")
                
                profile = await self.analyze_resume(
                    resume_content=resume_content,
                    http_client=http_client,
                    model_name=model_name
                )
                
                requirements = await self.analyze_job(
                    job_description=job_description,
                    http_client=http_client,
                    model_name=model_name
                )
            
            logger.info("Service: Resume customization completed")
            return optimized_resume, profile, requirements
        
        except Exception as e:
            error_msg = f"Resume customization failed in service: {str(e)}"
            logger.error(error_msg)
            raise ResumeCustomizerException(error_msg)


# Instantiate the service
customizer_service = CustomizerService()
