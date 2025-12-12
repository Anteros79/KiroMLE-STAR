"""Property-based tests for inner loop selection logic.

Feature: mle-star-agent, Property 7: Inner loop selects best performer
Validates: Requirements 7.4, 7.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from mle_star.models.data_models import RefinementAttempt
from mle_star.tools.refinement_utils import (
    select_best_attempt,
    get_best_solution_code,
    InnerLoopResult,
)


# Strategy for generating valid validation scores (reasonable ML metric values)
score_strategy = st.floats(
    min_value=0.0,
    max_value=1.0,
    allow_nan=False,
    allow_infinity=False,
)

# Strategy for generating plan text
plan_strategy = st.text(min_size=5, max_size=200).filter(lambda x: x.strip())

# Strategy for generating code blocks
code_strategy = st.text(min_size=10, max_size=500).filter(lambda x: x.strip())


def create_refinement_attempt(
    plan: str,
    score: float,
    iteration: int,
    code_block: str = "refined_code",
    full_solution: str = "full_solution_code",
) -> RefinementAttempt:
    """Create a RefinementAttempt with the given parameters."""
    return RefinementAttempt(
        plan=plan,
        refined_code_block=code_block,
        full_solution=full_solution,
        validation_score=score,
        iteration=iteration,
    )


# Strategy for generating a single refinement attempt
refinement_attempt_strategy = st.builds(
    create_refinement_attempt,
    plan=plan_strategy,
    score=score_strategy,
    iteration=st.integers(min_value=0, max_value=100),
    code_block=code_strategy,
    full_solution=code_strategy,
)


class TestInnerLoopSelection:
    """Property tests for inner loop selection logic.
    
    Feature: mle-star-agent, Property 7: Inner loop selects best performer
    Validates: Requirements 7.4, 7.5
    """
    
    @given(
        attempts=st.lists(
            refinement_attempt_strategy,
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_best_attempt_has_highest_score(
        self, attempts: list[RefinementAttempt]
    ):
        """Property 7: The selected candidate has the highest validation score.
        
        Feature: mle-star-agent, Property 7: Inner loop selects best performer
        Validates: Requirements 7.4
        
        For any refinement inner loop with multiple attempts, the selected
        candidate SHALL have a validation score greater than or equal to
        all other attempts in that loop.
        """
        # Ensure we have valid attempts
        assume(len(attempts) >= 1)
        assume(all(a.plan.strip() for a in attempts))
        
        # Select the best attempt
        result = select_best_attempt(attempts)
        
        # Property: best_attempt is not None when attempts exist
        assert result.best_attempt is not None, \
            "best_attempt should not be None when attempts exist"
        
        # Property: best_score equals the best_attempt's score
        assert result.best_score == result.best_attempt.validation_score, \
            f"best_score ({result.best_score}) should equal best_attempt's score ({result.best_attempt.validation_score})"
        
        # Property: best_attempt has score >= all other attempts
        for attempt in attempts:
            assert result.best_attempt.validation_score >= attempt.validation_score, \
                f"Best attempt score ({result.best_attempt.validation_score}) should be >= all attempts, but found {attempt.validation_score}"
    
    @given(
        attempts=st.lists(
            refinement_attempt_strategy,
            min_size=2,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_best_attempt_is_from_attempts_list(
        self, attempts: list[RefinementAttempt]
    ):
        """Property 7: The selected candidate is one of the attempts.
        
        Feature: mle-star-agent, Property 7: Inner loop selects best performer
        Validates: Requirements 7.4
        
        The selected best attempt must be one of the original attempts,
        not a fabricated or modified attempt.
        """
        assume(len(attempts) >= 2)
        assume(all(a.plan.strip() for a in attempts))
        
        result = select_best_attempt(attempts)
        
        # Property: best_attempt is in the original attempts list
        assert result.best_attempt is not None
        
        # Check that the best attempt matches one of the original attempts
        found = False
        for attempt in attempts:
            if (attempt.plan == result.best_attempt.plan and
                attempt.validation_score == result.best_attempt.validation_score and
                attempt.iteration == result.best_attempt.iteration):
                found = True
                break
        
        assert found, "best_attempt should be one of the original attempts"
    
    @given(
        attempts=st.lists(
            refinement_attempt_strategy,
            min_size=1,
            max_size=10,
        ),
        initial_score=score_strategy,
    )
    @settings(max_examples=100)
    def test_improved_flag_correctness(
        self, attempts: list[RefinementAttempt], initial_score: float
    ):
        """Property 7: The improved flag correctly indicates improvement.
        
        Feature: mle-star-agent, Property 7: Inner loop selects best performer
        Validates: Requirements 7.5
        
        When a refinement improves performance, the system correctly
        identifies this improvement.
        """
        assume(len(attempts) >= 1)
        assume(all(a.plan.strip() for a in attempts))
        
        result = select_best_attempt(attempts, initial_score=initial_score)
        
        # Property: improved is True iff best_score > initial_score
        expected_improved = result.best_score > initial_score
        assert result.improved == expected_improved, \
            f"improved flag ({result.improved}) should be {expected_improved} when best_score={result.best_score} and initial_score={initial_score}"


    @given(
        attempts=st.lists(
            refinement_attempt_strategy,
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_all_attempts_preserved(
        self, attempts: list[RefinementAttempt]
    ):
        """Property 7: All attempts are preserved in the result.
        
        Feature: mle-star-agent, Property 7: Inner loop selects best performer
        Validates: Requirements 7.4
        
        The result should contain all original attempts for audit/logging.
        """
        assume(len(attempts) >= 1)
        assume(all(a.plan.strip() for a in attempts))
        
        result = select_best_attempt(attempts)
        
        # Property: all_attempts has same length as input
        assert len(result.all_attempts) == len(attempts), \
            f"all_attempts length ({len(result.all_attempts)}) should equal input length ({len(attempts)})"


class TestGetBestSolutionCode:
    """Property tests for get_best_solution_code function.
    
    Feature: mle-star-agent, Property 7: Inner loop selects best performer
    Validates: Requirements 7.4, 7.5
    """
    
    @given(
        attempts=st.lists(
            refinement_attempt_strategy,
            min_size=1,
            max_size=10,
        ),
        fallback=code_strategy,
    )
    @settings(max_examples=100)
    def test_returns_best_solution_code(
        self, attempts: list[RefinementAttempt], fallback: str
    ):
        """Property 7: Returns the solution code from the best attempt.
        
        Feature: mle-star-agent, Property 7: Inner loop selects best performer
        Validates: Requirements 7.5
        """
        assume(len(attempts) >= 1)
        assume(all(a.plan.strip() for a in attempts))
        assume(fallback.strip())
        
        code = get_best_solution_code(attempts, fallback)
        
        # Find the expected best attempt
        best_attempt = max(attempts, key=lambda a: a.validation_score)
        
        # Property: returned code is from the best attempt
        assert code == best_attempt.full_solution, \
            "Returned code should be from the best-scoring attempt"
    
    @given(fallback=code_strategy)
    @settings(max_examples=100)
    def test_returns_fallback_when_empty(self, fallback: str):
        """Property 7: Returns fallback when no attempts exist.
        
        Feature: mle-star-agent, Property 7: Inner loop selects best performer
        Validates: Requirements 7.5
        """
        assume(fallback.strip())
        
        code = get_best_solution_code([], fallback)
        
        # Property: returns fallback when no attempts
        assert code == fallback, \
            "Should return fallback code when no attempts exist"


class TestEmptyAttempts:
    """Edge case tests for empty attempts list.
    
    Feature: mle-star-agent, Property 7: Inner loop selects best performer
    Validates: Requirements 7.4
    """
    
    def test_empty_attempts_returns_none_best(self):
        """Empty attempts list should return None for best_attempt."""
        result = select_best_attempt([])
        
        assert result.best_attempt is None
        assert len(result.all_attempts) == 0
        assert result.improved is False
    
    @given(initial_score=score_strategy)
    @settings(max_examples=100)
    def test_empty_attempts_preserves_initial_score(self, initial_score: float):
        """Empty attempts should preserve initial score as best_score."""
        result = select_best_attempt([], initial_score=initial_score)
        
        assert result.best_score == initial_score
        assert result.improved is False
