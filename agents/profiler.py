"""Profiler agent implementation for Resume Customizer."""
from typing import Dict, List, Optional, Union

from pydantic_ai import RunContext
from pydantic_ai.usage import Usage, UsageLimits

from agents.base import BaseAgent
from agents.models.profile import ProfessionalProfile
from core.utils.file_detection import detect_file_type
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager
from infrastructure.document_processor import DocumentProcessor


class ProfilerAgent(BaseAgent):
    """Agent for analyzing resumes and creating professional profiles."""
    
    def __init__(self, prompt_manager: PromptManager):
        """Initialize profiler agent.
        
        Args:
            prompt_manager: Manager for prompt templates
        """
        super().__init__(prompt_manager, "profiler", ProfessionalProfile)
        self.document_processor = DocumentProcessor()
        
        # Tool for extracting text from resume files
        @self.agent.tool
        async def extract_resume_text(
            ctx: RunContext[ResumeCustomizerDeps], 
            file_content: bytes,
            file_type: Optional[str] = None,
            filename: Optional[str] = None
        ) -> str:
            """Process and extract text from resume files.
            
            Args:
                ctx: Run context
                file_content: Binary content of the file
                file_type: MIME type of the file (optional)
                filename: Original filename (optional)
                
            Returns:
                str: Extracted text from the document
            """
            # Input validation
            if not isinstance(file_content, bytes):
                self.log_error(f"Invalid file_content type: {type(file_content)}")
                raise ValueError("file_content must be bytes")
                
            if len(file_content) == 0:
                self.log_error("Empty file content")
                raise ValueError("File content is empty")
            
            # Detect file type
            detected_type = detect_file_type(file_content, file_type, filename)
            self.log_info(f"Detected file type: {detected_type}")
                
            # Extract text
            try:
                text = await self.document_processor.extract_text_from_bytes(
                    file_content, detected_type, filename
                )
                self.log_info(f"Successfully extracted {len(text)} characters from document")
                return text
            except Exception as e:
                self.log_error(f"Error extracting text: {str(e)}")
                raise ValueError(f"Failed to extract text from document: {str(e)}")
    
    def _get_fallback_prompt(self) -> str:
        """Get fallback system prompt for profiler agent.
        
        Returns:
            str: Fallback system prompt
        """
        return (
            "You are Dr. Maya Kaplan, a Career Intelligence Specialist with a Ph.D. "
            "in Industrial-Organizational Psychology and 12 years of experience in "
            "talent acquisition analytics at Fortune 500 companies. "
            "\n\n"
            "Your task is to analyze a resume and extract a comprehensive professional "
            "profile that identifies core skills, experiences, and unique value propositions. "
            "You focus on evidence-based assessment and ignore exaggerated claims. "
            "\n\n"
            "Extract all relevant professional information and organize it into a structured "
            "profile following the ProfessionalProfile schema. Be specific, detailed, and "
            "focus on concrete evidence rather than vague claims."
        )
    
    async def analyze_resume(
        self, 
        resume_content: str,
        deps: ResumeCustomizerDeps,
        usage: Optional[Usage] = None,
        usage_limits: Optional[UsageLimits] = None
    ) -> ProfessionalProfile:
        """Analyze a resume and extract a professional profile.
        
        Args:
            resume_content: Text content of the resume
            deps: Agent dependencies
            usage: Optional usage tracker
            usage_limits: Optional usage limits
            
        Returns:
            ProfessionalProfile: Structured profile of the candidate
        """
        return await self.run(
            resume_content,
            deps=deps,
            usage=usage,
            usage_limits=usage_limits,
            extra_context={"operation": "analyze_resume", "content_length": len(resume_content)}
        )
    
    async def analyze_resume_file(
        self, 
        file_content: bytes,
        file_type: Optional[str] = None,
        deps: ResumeCustomizerDeps = None,
        usage: Optional[Usage] = None,
        usage_limits: Optional[UsageLimits] = None,
        filename: Optional[str] = None
    ) -> ProfessionalProfile:
        """Analyze a resume file and extract a professional profile.
        
        Args:
            file_content: Binary content of the resume file
            file_type: MIME type of the file (optional)
            deps: Agent dependencies
            usage: Optional usage tracker
            usage_limits: Optional usage limits
            filename: Original filename (optional)
            
        Returns:
            ProfessionalProfile: Structured profile of the candidate
        """
        # Detect file type
        detected_type = detect_file_type(file_content, file_type, filename)
        self.log_info(f"Analyzing resume file of type {detected_type}")
        
        # Extract text from the file
        text = await self.document_processor.extract_text_from_bytes(
            file_content, detected_type, filename
        )
        
        # Analyze the extracted text
        return await self.analyze_resume(text, deps, usage, usage_limits)
