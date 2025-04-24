"""API dependencies."""
import time
from typing import Callable, Dict, Generator, Optional, AsyncGenerator

from fastapi import Depends, HTTPException, status

from agents.profiler import ProfilerAgent
from agents.researcher import ResearcherAgent
from agents.strategist import StrategistAgent
from core.config import get_settings
from core.exceptions import ResumeCustomizerError
from infrastructure.ai_provider import AIProvider, PromptManager
from infrastructure.document_processor import DocumentProcessor, DocumentBuilder
from services.customizer import ResumeCustomizerService
from services.document import DocumentService


# Application state
start_time = time.time()


# Dependencies
def get_prompt_manager() -> PromptManager:
    """Get prompt manager instance.
    
    Returns:
        PromptManager: Prompt manager instance
    """
    return PromptManager()


def get_document_processor() -> DocumentProcessor:
    """Get document processor instance.
    
    Returns:
        DocumentProcessor: Document processor instance
    """
    return DocumentProcessor()


def get_document_builder() -> DocumentBuilder:
    """Get document builder instance.
    
    Returns:
        DocumentBuilder: Document builder instance
    """
    return DocumentBuilder()


async def get_ai_provider() -> AsyncGenerator[AIProvider, None]:
    """Get AI provider instance.
    
    Yields:
        AIProvider: AI provider instance
    """
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenRouter API key not configured"
        )
    
    provider = AIProvider(
        api_key=settings.openrouter_api_key,
        default_model=settings.default_model
    )
    
    try:
        yield provider
    finally:
        await provider.close()


def get_profiler_agent(
    prompt_manager: PromptManager = Depends(get_prompt_manager)
) -> ProfilerAgent:
    """Get profiler agent instance.
    
    Args:
        prompt_manager: Prompt manager instance
        
    Returns:
        ProfilerAgent: Profiler agent instance
    """
    return ProfilerAgent(prompt_manager=prompt_manager)


def get_researcher_agent(
    prompt_manager: PromptManager = Depends(get_prompt_manager)
) -> ResearcherAgent:
    """Get researcher agent instance.
    
    Args:
        prompt_manager: Prompt manager instance
        
    Returns:
        ResearcherAgent: Researcher agent instance
    """
    return ResearcherAgent(prompt_manager=prompt_manager)


def get_strategist_agent(
    profiler_agent: ProfilerAgent = Depends(get_profiler_agent),
    researcher_agent: ResearcherAgent = Depends(get_researcher_agent),
    prompt_manager: PromptManager = Depends(get_prompt_manager)
) -> StrategistAgent:
    """Get strategist agent instance.
    
    Args:
        profiler_agent: Profiler agent instance
        researcher_agent: Researcher agent instance
        prompt_manager: Prompt manager instance
        
    Returns:
        StrategistAgent: Strategist agent instance
    """
    return StrategistAgent(
        profiler_agent=profiler_agent,
        researcher_agent=researcher_agent,
        prompt_manager=prompt_manager
    )


def get_document_service(
    document_processor: DocumentProcessor = Depends(get_document_processor),
    document_builder: DocumentBuilder = Depends(get_document_builder)
) -> DocumentService:
    """Get document service instance.
    
    Args:
        document_processor: Document processor instance
        document_builder: Document builder instance
        
    Returns:
        DocumentService: Document service instance
    """
    return DocumentService(
        document_processor=document_processor,
        document_builder=document_builder
    )


async def get_resume_customizer_service(
    strategist_agent: StrategistAgent = Depends(get_strategist_agent),
    ai_provider: AIProvider = Depends(get_ai_provider),
    document_processor: DocumentProcessor = Depends(get_document_processor)
) -> ResumeCustomizerService:
    """Get resume customizer service instance.
    
    Args:
        strategist_agent: Strategist agent instance
        ai_provider: AI provider instance
        document_processor: Document processor instance
        
    Returns:
        ResumeCustomizerService: Resume customizer service instance
    """
    return ResumeCustomizerService(
        strategist_agent=strategist_agent,
        ai_provider=ai_provider,
        document_processor=document_processor
    )


def get_uptime() -> float:
    """Get application uptime in seconds.
    
    Returns:
        float: Uptime in seconds
    """
    return time.time() - start_time
