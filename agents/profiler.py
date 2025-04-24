"""Profiler agent implementation for Resume Customizer."""
from typing import Dict, List, Optional, Union

from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import Usage, UsageLimits

from agents.models.profile import ProfessionalProfile
from core.logging import LoggerMixin
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager
from infrastructure.document_processor import DocumentProcessor


class ProfilerAgent(LoggerMixin):
    """Agent for analyzing resumes and creating professional profiles."""
    
    def __init__(self, prompt_manager: PromptManager):
        """Initialize profiler agent.
        
        Args:
            prompt_manager: Manager for prompt templates
        """
        self.prompt_manager = prompt_manager
        self.document_processor = DocumentProcessor()
        
        # Initialize the Pydantic AI agent
        self.agent = Agent(
            'test',  # Use test model for unit tests 
            deps_type=ResumeCustomizerDeps,
            output_type=ProfessionalProfile,
            system_prompt=self._get_system_prompt(),
        )
        
        # Set dynamic system prompt for model configuration
        @self.agent.system_prompt
        async def set_model(ctx: RunContext[ResumeCustomizerDeps]) -> str:
            """Set the specific model to use via dynamic system prompt."""
            return f"You will be using the {ctx.deps.model_name} model to analyze resumes."
        
        # Tool for extracting text from resume files
        @self.agent.tool
        async def extract_resume_text(
            ctx: RunContext[ResumeCustomizerDeps], 
            file_content: bytes,
            file_type: str
        ) -> str:
            """Process and extract text from resume files."""
            return await self.document_processor.extract_text_from_bytes(file_content, file_type)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the profiler agent.
        
        Returns:
            str: System prompt
        """
        try:
            return self.prompt_manager.get_template("profiler", "latest")
        except Exception:
            # Fallback to default prompt if template not found
            self.log_info("Using default profiler prompt")
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
        self.log_info("Analyzing resume")
        
        result = await self.agent.run(
            resume_content,
            deps=deps,
            usage=usage,
            usage_limits=usage_limits
        )
        
        self.log_info("Resume analysis complete")
        return result.output
    
    async def analyze_resume_file(
        self, 
        file_content: bytes,
        file_type: str,
        deps: ResumeCustomizerDeps,
        usage: Optional[Usage] = None,
        usage_limits: Optional[UsageLimits] = None
    ) -> ProfessionalProfile:
        """Analyze a resume file and extract a professional profile.
        
        Args:
            file_content: Binary content of the resume file
            file_type: MIME type of the file
            deps: Agent dependencies
            usage: Optional usage tracker
            usage_limits: Optional usage limits
            
        Returns:
            ProfessionalProfile: Structured profile of the candidate
        """
        self.log_info(f"Analyzing resume file of type {file_type}")
        
        # Extract text from the file
        text = await self.document_processor.extract_text_from_bytes(file_content, file_type)
        
        # Analyze the extracted text
        return await self.analyze_resume(text, deps, usage, usage_limits)
