"""Resume customization service."""
from typing import Dict, Optional, Tuple

from pydantic_ai.usage import Usage, UsageLimits

from agents.models.resume import CustomizationRequest, CustomizationResponse, OptimizedResume, ResumeFormat
from agents.strategist import StrategistAgent
from core.exceptions import AIProviderError, ConfigurationError, TokenLimitExceededError
from core.logging import LoggerMixin
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
            AIProviderError: If there's an error with the AI provider
            TokenLimitExceededError: If token limit is exceeded
        """
        self.log_info(f"Processing resume customization request using model {request.model_name}")
        
        # Create usage tracker
        usage = Usage()
        
        # Set usage limits if specified
        usage_limits = None
        if request.max_tokens:
            usage_limits = UsageLimits(total_tokens_limit=request.max_tokens)
        
        try:
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
            
        except Exception as e:
            self.log_error(f"Error customizing resume: {str(e)}")
            raise
    
    async def customize_resume_from_file(
        self,
        file_content: bytes,
        file_type: str,
        job_description: str,
        model_name: str = "deepseek/deepseek-r1-distill-llama-70b",
        output_format: ResumeFormat = ResumeFormat.MARKDOWN,
        max_tokens: Optional[int] = None
    ) -> CustomizationResponse:
        """Customize a resume from file for a specific job description.
        
        Args:
            file_content: Binary content of the resume file
            file_type: MIME type of the file
            job_description: Text content of the job description
            model_name: Name of the AI model to use
            output_format: Desired output format
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            CustomizationResponse: Customization response with optimized resume
        """
        # Validate inputs
        if not file_content or len(file_content) == 0:
            self.log_error("Empty file content provided")
            raise DocumentProcessingError("Empty file content provided")
            
        if not isinstance(file_type, str) or len(file_type.strip()) == 0:
            self.log_warning(f"Invalid file_type: {file_type!r}, using default")
            file_type = "application/octet-stream"
            
        self.log_info(f"Processing resume customization from file of type {file_type} with size {len(file_content)} bytes")
        
        # Always check for PDF signature first
        if len(file_content) >= 4 and file_content[:4] == b'%PDF':
            self.log_info("PDF signature detected, processing as PDF regardless of MIME type")
            file_type = "application/pdf"
        # Check for DOCX signature (PK zip header)
        elif len(file_content) >= 2 and file_content[:2] == b'PK':
            self.log_info("DOCX/ZIP signature detected, attempting to process as DOCX")
            file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        # Process plain text files directly if possible
        if file_type == "text/plain":
            try:
                resume_content = file_content.decode('utf-8')
                self.log_debug(f"Decoded text file: {resume_content[:50]}...")
            except UnicodeDecodeError:
                self.log_warning("Failed to decode text file, trying to extract text with processor")
                resume_content = await self.document_processor.extract_text_from_bytes(
                    file_content, file_type
                )
        else:
            # Extract text from file using document processor
            try:
                self.log_info(f"Extracting text from file using document processor with type: {file_type}")
                resume_content = await self.document_processor.extract_text_from_bytes(
                    file_content, file_type
                )
                self.log_info(f"Successfully extracted {len(resume_content)} characters from document")
            except DocumentProcessingError as e:
                self.log_error(f"Error in document processor: {str(e)}")
                # Try one more time with generic file type as fallback
                if file_type != "application/octet-stream":
                    self.log_warning("Retrying with generic file type")
                    resume_content = await self.document_processor.extract_text_from_bytes(
                        file_content, "application/octet-stream"
                    )
                else:
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
