"""Tests for the prompt management system."""
import pytest

from infrastructure.ai_provider import PromptManager, PromptTemplate
from core.exceptions import AIProviderError


def test_prompt_manager_init() -> None:
    """Test prompt manager initialization."""
    # Initialize prompt manager
    manager = PromptManager()
    
    # Check properties
    assert manager.templates == {}


def test_prompt_manager_add_template() -> None:
    """Test adding templates to prompt manager."""
    # Initialize prompt manager
    manager = PromptManager()
    
    # Add a template
    template = PromptTemplate(
        version="1.0.0",
        template="Test prompt",
        description="Test description"
    )
    manager.add_template("test", template)
    
    # Check template was added
    assert "test" in manager.templates
    assert "1.0.0" in manager.templates["test"]
    assert manager.templates["test"]["1.0.0"] == template


def test_prompt_manager_add_multiple_versions() -> None:
    """Test adding multiple versions of templates."""
    # Initialize prompt manager
    manager = PromptManager()
    
    # Add templates with different versions
    template1 = PromptTemplate(
        version="1.0.0",
        template="Test prompt v1",
        description="Test description v1"
    )
    template2 = PromptTemplate(
        version="2.0.0",
        template="Test prompt v2",
        description="Test description v2"
    )
    
    manager.add_template("test", template1)
    manager.add_template("test", template2)
    
    # Check templates were added
    assert "test" in manager.templates
    assert "1.0.0" in manager.templates["test"]
    assert "2.0.0" in manager.templates["test"]
    assert manager.templates["test"]["1.0.0"] == template1
    assert manager.templates["test"]["2.0.0"] == template2


def test_prompt_manager_get_template() -> None:
    """Test getting templates from prompt manager."""
    # Initialize prompt manager
    manager = PromptManager()
    
    # Add templates with different versions
    template1 = PromptTemplate(
        version="1.0.0",
        template="Test prompt v1",
        description="Test description v1"
    )
    template2 = PromptTemplate(
        version="2.0.0",
        template="Test prompt v2",
        description="Test description v2"
    )
    
    manager.add_template("test", template1)
    manager.add_template("test", template2)
    
    # Get template by version
    prompt1 = manager.get_template("test", "1.0.0")
    prompt2 = manager.get_template("test", "2.0.0")
    
    # Check templates
    assert prompt1 == "Test prompt v1"
    assert prompt2 == "Test prompt v2"


def test_prompt_manager_get_latest_template() -> None:
    """Test getting latest template version."""
    # Initialize prompt manager
    manager = PromptManager()
    
    # Add templates with different versions
    template1 = PromptTemplate(
        version="1.0.0",
        template="Test prompt v1",
        description="Test description v1"
    )
    template2 = PromptTemplate(
        version="1.1.0",
        template="Test prompt v1.1",
        description="Test description v1.1"
    )
    template3 = PromptTemplate(
        version="2.0.0",
        template="Test prompt v2",
        description="Test description v2"
    )
    
    manager.add_template("test", template1)
    manager.add_template("test", template2)
    manager.add_template("test", template3)
    
    # Get latest template
    prompt = manager.get_template("test", "latest")
    
    # Check template is the latest version
    assert prompt == "Test prompt v2"


def test_prompt_manager_get_template_error() -> None:
    """Test error handling when getting templates."""
    # Initialize prompt manager
    manager = PromptManager()
    
    # Try to get template for non-existent agent
    with pytest.raises(AIProviderError):
        manager.get_template("non_existent")
    
    # Add a template
    template = PromptTemplate(
        version="1.0.0",
        template="Test prompt",
        description="Test description"
    )
    manager.add_template("test", template)
    
    # Try to get non-existent version
    with pytest.raises(AIProviderError):
        manager.get_template("test", "non_existent")
