"""Tests for prompt initialization."""
import pytest

from infrastructure.init_prompts import init_prompt_manager


def test_init_prompt_manager() -> None:
    """Test initializing prompt manager with default prompts."""
    # Initialize prompt manager
    manager = init_prompt_manager()
    
    # Check that the manager has templates for all agents
    assert "profiler" in manager.templates
    assert "researcher" in manager.templates
    assert "strategist" in manager.templates
    
    # Check that each agent has at least one template version
    assert len(manager.templates["profiler"]) > 0
    assert len(manager.templates["researcher"]) > 0
    assert len(manager.templates["strategist"]) > 0
    
    # Check that the latest template for each agent is accessible
    profiler_prompt = manager.get_template("profiler", "latest")
    researcher_prompt = manager.get_template("researcher", "latest")
    strategist_prompt = manager.get_template("strategist", "latest")
    
    # Check that the prompts contain expected content
    assert "Dr. Maya Kaplan" in profiler_prompt
    assert "Eliza Chen" in researcher_prompt
    assert "CareerPeak" in strategist_prompt
