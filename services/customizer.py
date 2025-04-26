"""Resume customization service."""
from typing import Dict, Optional, Tuple

from pydantic_ai.usage import Usage, UsageLimits

from agents.models.resume import CustomizationRequest, CustomizationResponse, OptimizedResume, ResumeFormat
from agents.strategist import StrategistAgent
from core.exceptions import AIProviderError, ConfigurationError, TokenLimitExceededError, DocumentProcessingError
from core.logging import LoggerMixin
from core.utils.file_detection import detect_file_type, PDF_MIME_TYPE, DOCX_MIME_TYPE, TEXT_MIME_TYPE
from infrastructure.ai_provider import AIProvider
from infrastructure.document_processor import DocumentProcessor


class ResumeCustomizerService(LoggerMixin):
    """Service for customizing resumes for job descriptions."""
    
    def __init__(
        self, 
        strategist_agent: StrategistAgent,
        ai_provider: AIProvider,
        document_processor: DocumentProcessor
    ):
        """Initialize resume customizer service.
        
        Args:
            strategist_agent: Strategist agent instance
            ai_provider: AI provider instance
            document_processor: Document processor instance
        """
        self.strategist_agent = strategist_agent
        self.ai_provider = ai_provider
        self.document_processor = document_processor
    
    @LoggerMixin.log_operation("resume_customization")
    async def customize_resume(
        self, 
        request: CustomizationRequest
    ) -> CustomizationResponse:
        """Customize a resume for a specific job description.
        
        Args:
            request: Customization request
            
        Returns:
            CustomizationResponse: Customization response with optimized resume
            
        Raises:
            ConfigurationError: If API key is missing
            ServiceError: If there's an error with the AI provider
            TokenLimitExceededError: If token limit is exceeded
        """
        self.log_info(f"Processing resume customization request using model {request.model_name}")
        
        # Create usage tracker
        usage = Usage()
        
        # Set usage limits if specified
        usage_limits = None
        if request.max_tokens:
            usage_limits = UsageLimits(total_tokens_limit=request.max_tokens)
        
        # Create dependencies for agent
        deps = await self.ai_provider.create_deps(model_name=request.model_name)
        
        # Optimize resume
        optimized_resume = await self.strategist_agent.optimize_resume(
            resume_content=request.resume_content,
            job_description=request.job_description,
            deps=deps,
            output_format=request.output_format,
            usage=usage,
            usage_limits=usage_limits
        )
        
        # Create response
        response = CustomizationResponse(
            optimized_resume=optimized_resume,
            usage_stats={
                "requests": usage.requests,
                "request_tokens": usage.request_tokens,
                "response_tokens": usage.response_tokens,
                "total_tokens": usage.total_tokens
            }
        )
        
        self.log_info(
            "Resume customization complete", 
            extra={"total_tokens": usage.total_tokens}
        )
        
        return response
    
    @LoggerMixin.log_operation("file_resume_customization")
    async def customize_resume_from_file(
        self,
        file_content: bytes,
        file_type: Optional[str] = None,
        job_description: str = "",
        model_name: str = "deepseek/deepseek-r1-distill-llama-70b",
        output_format: ResumeFormat = ResumeFormat.MARKDOWN,
        max_tokens: Optional[int] = None,
        filename: Optional[str] = None
    ) -> CustomizationResponse:
        """Customize a resume from file for a specific job description.
        
        Args:
            file_content: Binary content of the resume file
            file_type: MIME type of the file (optional)
            job_description: Text content of the job description
            model_name: Name of the AI model to use
            output_format: Desired output format
            max_tokens: Maximum number of tokens to generate
            filename: Original filename (optional)
            
        Returns:
            CustomizationResponse: Customization response with optimized resume
        """
        # Validate inputs
        if not file_content or len(file_content) == 0:
            self.log_error("Empty file content provided")
            raise DocumentProcessingError("Empty file content provided")
            
        # Use the centralized file detection utility to determine file type
        actual_file_type = detect_file_type(file_content, file_type, filename)
            
        self.log_info(f"Processing resume customization from file of type {actual_file_type} with size {len(file_content)} bytes")
        
        # Extract text based on file type
        try:
            # First try using document processor which handles different formats
            self.log_info(f"Extracting text using document processor")
            resume_content = await self.document_processor.extract_text_from_bytes(
                file_content, actual_file_type, filename
            )
            self.log_info(f"Successfully extracted {len(resume_content)} characters from document")
        except Exception as e:
            self.log_error(f"Document processing error: {str(e)}")
            raise
        
        # Create request
        request = CustomizationRequest(
            resume_content=resume_content,
            job_description=job_description,
            model_name=model_name,
            output_format=output_format,
            max_tokens=max_tokens
        )
        
        # Process request
        return await self.customize_resume(request)
