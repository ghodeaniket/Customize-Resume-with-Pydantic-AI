"""Evaluation framework for AI agent outputs.

This module provides functionality for evaluating the quality of agent outputs
through automated validation, human feedback, and output scoring.
"""

import json
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable

from loguru import logger
from pydantic import BaseModel, Field, model_validator

from resume_customizer.core.config import settings


class FeedbackRating(str, Enum):
    """Rating options for user feedback."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    POOR = "poor"
    UNUSABLE = "unusable"


class FeedbackCategory(str, Enum):
    """Categories for user feedback."""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    FORMAT = "format"
    READABILITY = "readability"
    OTHER = "other"


class UserFeedback(BaseModel):
    """User feedback on agent output quality.
    
    Attributes:
        id: Unique identifier for the feedback
        session_id: Identifier for the user session
        agent_name: Name of the agent being evaluated
        prompt_version: Version of the prompt used
        rating: Overall quality rating
        categories: Specific categories being rated
        comments: Optional free-text comments
        created_at: Timestamp when the feedback was created
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    agent_name: str
    prompt_version: str
    rating: FeedbackRating
    categories: List[FeedbackCategory] = Field(default_factory=list)
    comments: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationResult(BaseModel):
    """Result of an automated validation check.
    
    Attributes:
        check_name: Name of the validation check
        passed: Whether the check passed
        score: Numeric score for the check (0-1)
        details: Optional details about the validation results
    """
    check_name: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    details: Optional[Dict[str, Any]] = None
    
    @model_validator(mode="after")
    def validate_score(self) -> "ValidationResult":
        """Ensure that score is 0 if not passed."""
        if not self.passed and self.score > 0:
            self.score = 0.0
        return self


class EvaluationResult(BaseModel):
    """Complete evaluation result for an agent output.
    
    Attributes:
        id: Unique identifier for the evaluation
        agent_name: Name of the agent being evaluated
        prompt_version: Version of the prompt used
        timestamp: When the evaluation was performed
        validations: Results of automated validations
        user_feedback: Optional user feedback
        overall_score: Calculated overall quality score
        metadata: Additional context about the evaluation
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    prompt_version: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    validations: List[ValidationResult] = Field(default_factory=list)
    user_feedback: Optional[UserFeedback] = None
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# In-memory storage for evaluation results
# In a production system, this would be stored in a database
_evaluation_results: List[EvaluationResult] = []
_user_feedback: List[UserFeedback] = []
_evaluation_lock = threading.RLock()

# Store validation criteria for each agent type
_validation_criteria: Dict[str, List[Dict[str, Any]]] = defaultdict(list)


def register_evaluation_criteria(
    agent_name: str,
    check_name: str,
    validator_func: Callable[[Any], ValidationResult],
    description: str,
    weight: float = 1.0
) -> None:
    """Register a validation criterion for an agent type.
    
    Args:
        agent_name: Name of the agent type (profiler, researcher, strategist)
        check_name: Name of the validation check
        validator_func: Function that performs validation and returns a ValidationResult
        description: Description of what the validation checks
        weight: Relative importance weight for this check in the overall score
    """
    with _evaluation_lock:
        _validation_criteria[agent_name].append({
            "check_name": check_name,
            "validator_func": validator_func,
            "description": description,
            "weight": weight
        })
    
    logger.info(f"Registered evaluation criterion '{check_name}' for {agent_name}")


async def evaluate_agent_output(
    agent_name: str,
    output: Any,
    prompt_version: str,
    metadata: Optional[Dict[str, Any]] = None
) -> EvaluationResult:
    """Evaluate the quality of an agent output.
    
    This function runs registered validation checks for the specified agent type
    and calculates an overall quality score.
    
    Args:
        agent_name: Name of the agent (profiler, researcher, strategist)
        output: The output to evaluate
        prompt_version: Version of the prompt used
        metadata: Additional context for the evaluation
        
    Returns:
        EvaluationResult: The evaluation results
    """
    with _evaluation_lock:
        # Get validation criteria for this agent type
        criteria = _validation_criteria.get(agent_name, [])
        
        # Create evaluation result container
        result = EvaluationResult(
            agent_name=agent_name,
            prompt_version=prompt_version,
            metadata=metadata or {}
        )
        
        # Run validations
        if criteria:
            total_weight = sum(c["weight"] for c in criteria)
            total_score = 0.0
            
            for criterion in criteria:
                try:
                    # Run the validator function
                    validation = await criterion["validator_func"](output)
                    result.validations.append(validation)
                    
                    # Add to weighted score
                    total_score += validation.score * (criterion["weight"] / total_weight)
                except Exception as e:
                    logger.warning(f"Validation '{criterion['check_name']}' failed: {str(e)}")
                    # Add a failed validation
                    result.validations.append(ValidationResult(
                        check_name=criterion["check_name"],
                        passed=False,
                        score=0.0,
                        details={"error": str(e)}
                    ))
            
            # Set overall score
            result.overall_score = total_score
        
        # Save the evaluation
        _evaluation_results.append(result)
        
        logger.info(f"Evaluated {agent_name} output: score={result.overall_score:.2f}")
        return result


async def collect_user_feedback(
    session_id: str,
    agent_name: str,
    prompt_version: str,
    rating: Union[FeedbackRating, str],
    categories: Optional[List[Union[FeedbackCategory, str]]] = None,
    comments: Optional[str] = None
) -> UserFeedback:
    """Collect user feedback on agent output quality.
    
    Args:
        session_id: Identifier for the user session
        agent_name: Name of the agent being evaluated
        prompt_version: Version of the prompt used
        rating: Overall quality rating
        categories: Specific categories being rated
        comments: Optional free-text comments
        
    Returns:
        UserFeedback: The recorded user feedback
    """
    # Handle string inputs
    if isinstance(rating, str):
        rating = FeedbackRating(rating)
    
    if categories:
        categories = [
            FeedbackCategory(cat) if isinstance(cat, str) else cat
            for cat in categories
        ]
    
    # Create feedback object
    feedback = UserFeedback(
        session_id=session_id,
        agent_name=agent_name,
        prompt_version=prompt_version,
        rating=rating,
        categories=categories or [],
        comments=comments
    )
    
    with _evaluation_lock:
        # Save the feedback
        _user_feedback.append(feedback)
        
        # Find any matching evaluation result and link the feedback
        for result in _evaluation_results:
            # This is a simplistic matching - in production, use proper session tracking
            if (result.agent_name == agent_name and
                result.prompt_version == prompt_version and
                result.metadata.get("session_id") == session_id):
                result.user_feedback = feedback
                break
    
    logger.info(f"Collected user feedback for {agent_name}: rating={rating}")
    return feedback


def get_evaluation_results(
    agent_name: Optional[str] = None,
    prompt_version: Optional[str] = None,
    min_score: Optional[float] = None,
    max_results: Optional[int] = None,
    include_feedback: bool = True
) -> List[Dict[str, Any]]:
    """Get evaluation results, optionally filtered.
    
    Args:
        agent_name: Optional filter by agent name
        prompt_version: Optional filter by prompt version
        min_score: Optional minimum score filter
        max_results: Optional limit on number of results
        include_feedback: Whether to include user feedback
        
    Returns:
        List of evaluation results as dictionaries
    """
    with _evaluation_lock:
        # Filter results
        filtered_results = _evaluation_results
        
        if agent_name:
            filtered_results = [r for r in filtered_results if r.agent_name == agent_name]
        
        if prompt_version:
            filtered_results = [r for r in filtered_results if r.prompt_version == prompt_version]
        
        if min_score is not None:
            filtered_results = [r for r in filtered_results if r.overall_score >= min_score]
        
        # Sort by timestamp (newest first)
        sorted_results = sorted(
            filtered_results,
            key=lambda r: r.timestamp,
            reverse=True
        )
        
        # Limit results
        if max_results:
            sorted_results = sorted_results[:max_results]
        
        # Convert to dictionaries
        result_dicts = []
        for result in sorted_results:
            result_dict = result.model_dump(exclude={"user_feedback"} if not include_feedback else set())
            result_dicts.append(result_dict)
        
        return result_dicts


# Initialize default validation criteria
def _initialize_default_validators():
    """Set up default validation criteria for each agent type."""
    # Helper for validator registration
    def register_validator(agent, name, func, desc, weight=1.0):
        register_evaluation_criteria(agent, name, func, desc, weight)
    
    # Profiler validators
    async def validate_profiler_completeness(output):
        """Check if profiler output contains all required fields with content."""
        data = output.model_dump()
        fields = ["core_identity", "technical_skills", "soft_skills",
                 "projects", "contribution_patterns", "interests", "work_style"]
        
        # Check how many fields are non-empty
        non_empty_fields = sum(1 for f in fields if data.get(f) and 
                               (not isinstance(data[f], list) or len(data[f]) > 0))
        
        # Score based on completeness
        completeness_score = non_empty_fields / len(fields)
        
        return ValidationResult(
            check_name="profiler_completeness",
            passed=completeness_score > 0.7,  # Require at least 70% completeness
            score=completeness_score,
            details={"fields_present": non_empty_fields, "total_fields": len(fields)}
        )
    
    async def validate_profiler_skills_detail(output):
        """Check if skills have sufficient detail."""
        tech_skills = output.technical_skills if hasattr(output, "technical_skills") else []
        soft_skills = output.soft_skills if hasattr(output, "soft_skills") else []
        
        # Check number of skills
        tech_count = len(tech_skills)
        soft_count = len(soft_skills)
        
        # Basic scoring based on number of skills identified
        score = min(1.0, (tech_count + soft_count) / 10)  # Aim for at least 10 skills total
        
        return ValidationResult(
            check_name="profiler_skills_detail",
            passed=score >= 0.5,  # At least 5 skills
            score=score,
            details={"technical_skills": tech_count, "soft_skills": soft_count}
        )
    
    # Researcher validators
    async def validate_researcher_completeness(output):
        """Check if researcher output contains all required fields with content."""
        data = output.model_dump()
        fields = ["company_profile", "core_requirements", "supplementary_attributes",
                 "hidden_expectations", "application_strategy", "keywords"]
        
        # Check how many fields are non-empty
        non_empty_fields = sum(1 for f in fields if data.get(f) and 
                               (not isinstance(data[f], list) or len(data[f]) > 0))
        
        # Score based on completeness
        completeness_score = non_empty_fields / len(fields)
        
        return ValidationResult(
            check_name="researcher_completeness",
            passed=completeness_score > 0.7,  # Require at least 70% completeness
            score=completeness_score,
            details={"fields_present": non_empty_fields, "total_fields": len(fields)}
        )
    
    async def validate_researcher_keywords(output):
        """Check if enough relevant keywords are extracted."""
        keywords = output.keywords if hasattr(output, "keywords") else []
        
        # Basic scoring based on number of keywords
        keyword_count = len(keywords)
        score = min(1.0, keyword_count / 15)  # Aim for at least 15 keywords
        
        return ValidationResult(
            check_name="researcher_keywords",
            passed=score >= 0.5,  # At least 7-8 keywords
            score=score,
            details={"keyword_count": keyword_count}
        )
    
    # Strategist validators
    async def validate_strategist_format(output):
        """Check if the output markdown is properly formatted."""
        # For a string output, check if it contains markdown elements
        if not isinstance(output, str):
            return ValidationResult(
                check_name="strategist_format",
                passed=False,
                score=0.0,
                details={"error": f"Expected string output, got {type(output)}"}
            )
        
        # Look for markdown headings and structure
        has_headings = "# " in output or "## " in output
        has_sections = output.count("\n\n") >= 3  # Multiple paragraphs
        has_formatting = "**" in output or "*" in output or "`" in output
        
        # Score based on markdown elements present
        elements = [has_headings, has_sections, has_formatting]
        format_score = sum(1 for e in elements if e) / len(elements)
        
        return ValidationResult(
            check_name="strategist_format",
            passed=format_score > 0.5,
            score=format_score,
            details={
                "has_headings": has_headings,
                "has_sections": has_sections,
                "has_formatting": has_formatting
            }
        )
    
    async def validate_strategist_content_length(output):
        """Check if the resume has sufficient content length."""
        if not isinstance(output, str):
            return ValidationResult(
                check_name="strategist_content_length",
                passed=False,
                score=0.0,
                details={"error": f"Expected string output, got {type(output)}"}
            )
        
        # Get word count
        words = len(output.split())
        
        # Score based on word count (most resumes should be 300-600 words)
        min_words = 300
        max_words = 1000
        
        if words < min_words:
            score = words / min_words
        elif words > max_words:
            score = max(0.0, 1.0 - (words - max_words) / max_words)
        else:
            score = 1.0
            
        return ValidationResult(
            check_name="strategist_content_length",
            passed=words >= min_words,
            score=score,
            details={"word_count": words, "min_expected": min_words, "max_expected": max_words}
        )
    
    # Register validators
    register_validator("profiler", "profiler_completeness", 
                      validate_profiler_completeness,
                      "Checks if all required fields are present and non-empty", 2.0)
    
    register_validator("profiler", "profiler_skills_detail", 
                      validate_profiler_skills_detail,
                      "Checks if skills have sufficient detail", 1.5)
    
    register_validator("researcher", "researcher_completeness", 
                      validate_researcher_completeness,
                      "Checks if all required fields are present and non-empty", 2.0)
    
    register_validator("researcher", "researcher_keywords", 
                      validate_researcher_keywords,
                      "Checks if enough relevant keywords are extracted", 1.5)
    
    register_validator("strategist", "strategist_format", 
                      validate_strategist_format,
                      "Checks if the output markdown is properly formatted", 1.0)
    
    register_validator("strategist", "strategist_content_length", 
                      validate_strategist_content_length,
                      "Checks if the resume has sufficient content", 1.5)


# Initialize default validators
_initialize_default_validators()
