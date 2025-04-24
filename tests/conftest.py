"""Test fixtures and configuration."""
import asyncio
import os
from typing import AsyncGenerator, Dict, Generator

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.profiler import ProfilerAgent
from agents.researcher import ResearcherAgent
from agents.strategist import StrategistAgent
from core.config import Settings, get_settings
from infrastructure.ai_provider import AIProvider, PromptManager, ResumeCustomizerDeps
from infrastructure.document_processor import DocumentProcessor, DocumentBuilder
from main import app as fastapi_app
from services.customizer import ResumeCustomizerService
from services.document import DocumentService


@pytest.fixture
def app() -> FastAPI:
    """Get FastAPI application.
    
    Returns:
        FastAPI: FastAPI application
    """
    return fastapi_app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Get test client.
    
    Args:
        app: FastAPI application
        
    Yields:
        TestClient: Test client
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings: Application settings
    """
    return get_settings()


@pytest.fixture
def prompt_manager() -> PromptManager:
    """Get prompt manager.
    
    Returns:
        PromptManager: Prompt manager instance
    """
    return PromptManager()


@pytest.fixture
def document_processor() -> DocumentProcessor:
    """Get document processor.
    
    Returns:
        DocumentProcessor: Document processor instance
    """
    return DocumentProcessor()


@pytest.fixture
def document_builder() -> DocumentBuilder:
    """Get document builder.
    
    Returns:
        DocumentBuilder: Document builder instance
    """
    return DocumentBuilder()


@pytest.fixture
def ai_provider(settings: Settings) -> AIProvider:
    """Get AI provider.
    
    Args:
        settings: Application settings
        
    Returns:
        AIProvider: AI provider instance
    """
    return AIProvider(
        api_key=settings.openrouter_api_key,
        default_model=settings.default_model
    )


@pytest.fixture
async def deps(ai_provider: AIProvider) -> AsyncGenerator[ResumeCustomizerDeps, None]:
    """Get agent dependencies.
    
    Args:
        ai_provider: AI provider instance
        
    Yields:
        ResumeCustomizerDeps: Agent dependencies
    """
    deps = await ai_provider.create_deps()
    try:
        yield deps
    finally:
        await deps.http_client.aclose()


@pytest.fixture
def profiler_agent(prompt_manager: PromptManager) -> ProfilerAgent:
    """Get profiler agent.
    
    Args:
        prompt_manager: Prompt manager instance
        
    Returns:
        ProfilerAgent: Profiler agent instance
    """
    return ProfilerAgent(prompt_manager=prompt_manager)


@pytest.fixture
def researcher_agent(prompt_manager: PromptManager) -> ResearcherAgent:
    """Get researcher agent.
    
    Args:
        prompt_manager: Prompt manager instance
        
    Returns:
        ResearcherAgent: Researcher agent instance
    """
    return ResearcherAgent(prompt_manager=prompt_manager)


@pytest.fixture
def strategist_agent(
    profiler_agent: ProfilerAgent,
    researcher_agent: ResearcherAgent,
    prompt_manager: PromptManager
) -> StrategistAgent:
    """Get strategist agent.
    
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


@pytest.fixture
def document_service(
    document_processor: DocumentProcessor,
    document_builder: DocumentBuilder
) -> DocumentService:
    """Get document service.
    
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


@pytest.fixture
def resume_customizer_service(
    strategist_agent: StrategistAgent,
    ai_provider: AIProvider,
    document_processor: DocumentProcessor
) -> ResumeCustomizerService:
    """Get resume customizer service.
    
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


@pytest.fixture
def sample_resume() -> str:
    """Get sample resume content.
    
    Returns:
        str: Sample resume content
    """
    return """
    Jane Smith
    Software Engineer
    
    Summary:
    Experienced software engineer with 5 years of experience in full-stack development.
    Proficient in Python, JavaScript, and cloud technologies.
    
    Experience:
    Senior Software Engineer, ABC Tech (2020-Present)
    - Led development of a microservices architecture using FastAPI and React
    - Improved system performance by 40% through optimizations
    - Mentored junior developers and conducted code reviews
    
    Software Engineer, XYZ Solutions (2018-2020)
    - Developed RESTful APIs using Django and PostgreSQL
    - Implemented CI/CD pipelines with Jenkins and Docker
    
    Education:
    Bachelor of Science in Computer Science, University of Technology (2018)
    
    Skills:
    - Python, JavaScript, TypeScript
    - React, Angular, Vue.js
    - FastAPI, Django, Flask
    - PostgreSQL, MongoDB
    - AWS, Docker, Kubernetes
    """


@pytest.fixture
def sample_job_description() -> str:
    """Get sample job description content.
    
    Returns:
        str: Sample job description content
    """
    return """
    Senior Software Engineer - Backend
    
    About the Role:
    We are looking for a Senior Software Engineer to join our backend team.
    In this role, you will design and implement high-performance APIs and microservices
    using Python and FastAPI. You will work closely with frontend developers and
    data scientists to build scalable and maintainable systems.
    
    Requirements:
    - 5+ years of experience in backend development
    - Strong proficiency in Python
    - Experience with FastAPI or similar frameworks (Django, Flask)
    - Solid understanding of RESTful API design
    - Experience with PostgreSQL and database optimization
    - Familiarity with containerization (Docker) and orchestration (Kubernetes)
    - Experience with cloud platforms (preferably AWS)
    
    Nice to Have:
    - Experience with real-time data processing
    - Knowledge of machine learning frameworks
    - Experience with GraphQL
    - Open-source contributions
    
    What We Offer:
    - Competitive salary and benefits
    - Remote-first work environment
    - Professional development opportunities
    - Collaborative and innovative team culture
    """
