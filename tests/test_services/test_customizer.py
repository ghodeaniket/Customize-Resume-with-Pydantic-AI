"""Tests for the resume customizer service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.models.resume import CustomizationRequest, CustomizationResponse, OptimizedResume, ResumeFormat
from agents.strategist import StrategistAgent
from infrastructure.ai_provider import AIProvider
from infrastructure.document_processor import DocumentProcessor
from services.customizer import ResumeCustomizerService
from core.exceptions import AIProviderError, TokenLimitExceededError


@pytest.mark.asyncio
async def test_resume_customizer_service_init(
    strategist_agent: StrategistAgent,
    ai_provider: AIProvider,
    document_processor: DocumentProcessor
) -> None:
    """Test resume customizer service initialization.
    
    Args:
        strategist_agent: Strategist agent instance
        ai_provider: AI provider instance
        document_processor: Document processor instance
    """
    # Initialize resume customizer service
    service = ResumeCustomizerService(
        strategist_agent=strategist_agent,
        ai_provider=ai_provider,
        document_processor=document_processor
    )
    
    # Check properties
    assert service.strategist_agent == strategist_agent
    assert service.ai_provider == ai_provider
    assert service.document_processor == document_processor


@pytest.mark.asyncio
async def test_customize_resume(
    strategist_agent: StrategistAgent,
    ai_provider: AIProvider,
    document_processor: DocumentProcessor,
    sample_resume: str,
    sample_job_description: str
) -> None:
    """Test customizing a resume.
    
    Args:
        strategist_agent: Strategist agent instance
        ai_provider: AI provider instance
        document_processor: Document processor instance
        sample_resume: Sample resume content
        sample_job_description: Sample job description content
    """
    # Initialize resume customizer service
    service = ResumeCustomizerService(
        strategist_agent=strategist_agent,
        ai_provider=ai_provider,
        document_processor=document_processor
    )
    
    # Create mock dependencies
    mock_deps = MagicMock()
    
    # Mock AI provider create_deps method
    with patch.object(ai_provider, 'create_deps', new_callable=AsyncMock) as mock_create_deps:
        mock_create_deps.return_value = mock_deps
        
        # Create mock optimized resume
        mock_optimized = OptimizedResume(
            content="# Optimized Resume\n\n...",
            format=ResumeFormat.MARKDOWN,
            sections=[],
            optimizations=["Optimization 1", "Optimization 2"],
            keywords_included=["Python", "FastAPI"],
            ats_score=95.0
        )
        
        # Mock strategist agent optimize_resume method
        with patch.object(strategist_agent, 'optimize_resume', new_callable=AsyncMock) as mock_optimize:
            mock_optimize.return_value = mock_optimized
            
            # Create customization request
            request = CustomizationRequest(
                resume_content=sample_resume,
                job_description=sample_job_description,
                model_name="test-model",
                output_format=ResumeFormat.MARKDOWN,
                max_tokens=4000
            )
            
            # Customize resume
            response = await service.customize_resume(request)
            
            # Check dependencies were created with the right model
            mock_create_deps.assert_called_once_with(model_name="test-model")
            
            # Check strategist agent was called with the right arguments
            mock_optimize.assert_called_once_with(
                resume_content=sample_resume,
                job_description=sample_job_description,
                deps=mock_deps,
                output_format=ResumeFormat.MARKDOWN,
                usage=pytest.approx(MagicMock),
                usage_limits=pytest.approx(MagicMock)
            )
            
            # Check response
            assert isinstance(response, CustomizationResponse)
            assert response.optimized_resume == mock_optimized
            assert response.usage_stats is not None


@pytest.mark.asyncio
async def test_customize_resume_from_file(
    strategist_agent: StrategistAgent,
    ai_provider: AIProvider,
    document_processor: DocumentProcessor,
    sample_job_description: str
) -> None:
    """Test customizing a resume from file.
    
    Args:
        strategist_agent: Strategist agent instance
        ai_provider: AI provider instance
        document_processor: Document processor instance
        sample_job_description: Sample job description content
    """
    # Initialize resume customizer service
    service = ResumeCustomizerService(
        strategist_agent=strategist_agent,
        ai_provider=ai_provider,
        document_processor=document_processor
    )
    
    # Create mock file content
    file_content = b"Sample file content"
    file_type = "application/pdf"
    
    # Create mock extracted text
    extracted_text = "Extracted resume text"
    
    # Mock document processor extract_text_from_bytes method
    with patch.object(document_processor, 'extract_text_from_bytes', new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = extracted_text
        
        # Create mock customization response
        mock_response = CustomizationResponse(
            optimized_resume=OptimizedResume(
                content="# Optimized Resume\n\n...",
                format=ResumeFormat.MARKDOWN
            ),
            usage_stats={"total_tokens": 1000}
        )
        
        # Mock customize_resume method
        with patch.object(service, 'customize_resume', new_callable=AsyncMock) as mock_customize:
            mock_customize.return_value = mock_response
            
            # Customize resume from file
            response = await service.customize_resume_from_file(
                file_content=file_content,
                file_type=file_type,
                job_description=sample_job_description,
                model_name="test-model",
                output_format=ResumeFormat.MARKDOWN,
                max_tokens=4000
            )
            
            # Check document processor was called with the right arguments
            mock_extract.assert_called_once_with(file_content, file_type)
            
            # Check customize_resume was called with the extracted text
            mock_customize.assert_called_once()
            request = mock_customize.call_args[0][0]
            assert request.resume_content == extracted_text
            assert request.job_description == sample_job_description
            assert request.model_name == "test-model"
            assert request.output_format == ResumeFormat.MARKDOWN
            assert request.max_tokens == 4000
            
            # Check response
            assert response == mock_response
