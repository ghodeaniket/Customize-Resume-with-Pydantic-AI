"""API endpoints for user feedback collection.

This module provides endpoints for collecting user feedback on agent outputs
and accessing feedback analytics.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Dict, List, Optional

from resume_customizer.api.dependencies import verify_api_key, get_admin_user
from resume_customizer.core.evaluation import (
    collect_user_feedback, 
    get_evaluation_results, 
    FeedbackRating,
    FeedbackCategory
)
from resume_customizer.core.config import settings


router = APIRouter()


class FeedbackRequest(BaseModel):
    """Request model for submitting user feedback.
    
    Attributes:
        session_id: Identifier for the user session
        agent_name: Name of the agent being evaluated
        prompt_version: Version of the prompt used
        rating: Overall quality rating
        categories: Specific categories being rated
        comments: Optional free-text comments
    """
    session_id: str
    agent_name: str
    prompt_version: str
    rating: str
    categories: Optional[List[str]] = None
    comments: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response model for feedback submission.
    
    Attributes:
        id: Unique identifier for the feedback
        message: Success message
    """
    id: str
    message: str


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    _: str = Depends(verify_api_key),
):
    """Submit user feedback on agent output quality.
    
    This endpoint allows users to provide feedback on the quality of the
    results they received from various agents.
    
    Args:
        feedback: The feedback details
        
    Returns:
        FeedbackResponse: Confirmation of feedback submission
    """
    try:
        # Validate the feedback rating
        rating = FeedbackRating(feedback.rating)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rating. Must be one of: {', '.join(r.value for r in FeedbackRating)}"
        )
    
    # Validate categories if provided
    categories = None
    if feedback.categories:
        try:
            categories = [FeedbackCategory(cat) for cat in feedback.categories]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {', '.join(c.value for c in FeedbackCategory)}"
            )
    
    # Record the feedback
    result = await collect_user_feedback(
        session_id=feedback.session_id,
        agent_name=feedback.agent_name,
        prompt_version=feedback.prompt_version,
        rating=rating,
        categories=categories,
        comments=feedback.comments
    )
    
    return FeedbackResponse(
        id=result.id,
        message="Feedback recorded successfully"
    )


@router.get("/analytics", response_model=Dict)
async def get_feedback_analytics(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    prompt_version: Optional[str] = Query(None, description="Filter by prompt version"),
    _: Dict = Depends(get_admin_user),
):
    """Get analytics on user feedback.
    
    This endpoint provides analytics on collected user feedback, including
    rating distributions and category breakdowns.
    
    Args:
        agent_name: Optional filter by agent name
        prompt_version: Optional filter by prompt version
        
    Returns:
        Dict: Feedback analytics
    """
    # Get evaluation results with feedback
    results = get_evaluation_results(
        agent_name=agent_name,
        prompt_version=prompt_version,
        include_feedback=True
    )
    
    # Extract feedback from results
    feedback_list = []
    for result in results:
        if result.get("user_feedback"):
            feedback_list.append(result["user_feedback"])
    
    # Count by rating
    rating_counts = {}
    for rating in FeedbackRating:
        rating_counts[rating.value] = sum(1 for f in feedback_list if f["rating"] == rating.value)
    
    # Count by category
    category_counts = {}
    for category in FeedbackCategory:
        category_counts[category.value] = sum(
            1 for f in feedback_list if category.value in f.get("categories", [])
        )
    
    # Calculate average scores
    rating_scores = {
        FeedbackRating.EXCELLENT.value: 1.0,
        FeedbackRating.GOOD.value: 0.75,
        FeedbackRating.NEUTRAL.value: 0.5,
        FeedbackRating.POOR.value: 0.25,
        FeedbackRating.UNUSABLE.value: 0.0
    }
    
    total_feedback = len(feedback_list)
    average_score = 0.0
    
    if total_feedback > 0:
        score_sum = sum(rating_scores[f["rating"]] for f in feedback_list)
        average_score = score_sum / total_feedback
    
    # Prepare the response
    return {
        "total_feedback": total_feedback,
        "average_score": average_score,
        "rating_distribution": rating_counts,
        "category_distribution": category_counts,
        "filtered_by": {
            "agent_name": agent_name,
            "prompt_version": prompt_version
        }
    }
