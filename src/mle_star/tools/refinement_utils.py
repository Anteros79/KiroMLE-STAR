"""Refinement utilities for MLE-STAR inner loop selection.

This module provides utility functions for selecting the best refinement
attempt from a list of attempts in the inner loop.
"""

from dataclasses import dataclass
from typing import Optional

from mle_star.models.data_models import RefinementAttempt


@dataclass
class InnerLoopResult:
    """Result of inner loop selection.
    
    Attributes:
        best_attempt: The refinement attempt with the highest validation score
        all_attempts: All attempts made during the inner loop
        best_score: The highest validation score achieved
        improved: Whether the best attempt improved over the initial score
    """
    best_attempt: Optional[RefinementAttempt]
    all_attempts: list[RefinementAttempt]
    best_score: float
    improved: bool


def select_best_attempt(
    attempts: list[RefinementAttempt],
    initial_score: Optional[float] = None,
) -> InnerLoopResult:
    """Select the best-performing refinement attempt from the inner loop.
    
    This function implements the inner loop selection logic as specified in
    Requirements 7.4 and 7.5:
    - 7.4: Select the best-performing candidate from all attempts
    - 7.5: Update the current best solution when a refinement improves performance
    
    Args:
        attempts: List of refinement attempts from the inner loop
        initial_score: Optional initial score before refinement (for comparison)
        
    Returns:
        InnerLoopResult containing the best attempt and metadata
    """
    if not attempts:
        return InnerLoopResult(
            best_attempt=None,
            all_attempts=[],
            best_score=initial_score if initial_score is not None else float("-inf"),
            improved=False,
        )
    
    # Find the attempt with the highest validation score
    best_attempt = max(attempts, key=lambda a: a.validation_score)
    best_score = best_attempt.validation_score
    
    # Determine if we improved over the initial score
    improved = False
    if initial_score is not None:
        improved = best_score > initial_score
    
    return InnerLoopResult(
        best_attempt=best_attempt,
        all_attempts=list(attempts),
        best_score=best_score,
        improved=improved,
    )


def get_best_solution_code(
    attempts: list[RefinementAttempt],
    fallback_code: str,
) -> str:
    """Get the solution code from the best refinement attempt.
    
    Args:
        attempts: List of refinement attempts
        fallback_code: Code to return if no attempts exist
        
    Returns:
        The full solution code from the best attempt, or fallback
    """
    result = select_best_attempt(attempts)
    
    if result.best_attempt is not None:
        return result.best_attempt.full_solution
    
    return fallback_code
