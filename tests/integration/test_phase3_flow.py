"""Integration tests for Phase 3: Ensemble flow.

Tests the ensemble planner → ensembler iteration.
Requirements: 9.1, 9.2
"""

import pytest

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import TaskDescription, EnsembleResult
from mle_star.graphs.ensemble import (
    EnsembleGraph,
    EnsembleState,
)
from mle_star.agents.ensemble_planner import (
    parse_ensemble_plan,
    EnsemblePlan,
    is_strategy_similar_to_previous,
)
from mle_star.agents.ensembler import (
    select_best_ensemble,
    EnsembleImplementationResult,
)


class TestPhase3Components:
    """Test individual Phase 3 components work correctly."""
    
    def test_parse_ensemble_plan_from_structured_response(self):
        """Test parsing ensemble plan from a well-structured response."""
        response = """
## Ensemble Strategy

### Strategy Name: Weighted Average Ensemble

### Description
Combine predictions from multiple models using weighted averaging based on validation scores.

### Implementation Steps
1. Train all base models on the training data
2. Generate predictions from each model on validation set
3. Calculate weights proportional to validation scores
4. Compute weighted average of predictions
5. Evaluate ensemble on validation set

### Weight Assignment
Weights are proportional to validation scores: w_i = score_i / sum(scores)

### Expected Benefit
Combining diverse models should reduce variance and improve generalization.
"""
        plan = parse_ensemble_plan(response)
        
        assert plan.success
        assert plan.strategy_name == "Weighted Average Ensemble"
        assert "weighted averaging" in plan.description.lower()
        assert len(plan.implementation_steps) >= 3
        assert plan.weight_assignment is not None
    
    def test_parse_ensemble_plan_extracts_steps(self):
        """Test that implementation steps are correctly extracted."""
        response = """
Strategy Name: Simple Averaging

Description
Average predictions from all models.

Implementation Steps
1. Load all models
2. Generate predictions
3. Average the predictions
4. Evaluate results
"""
        plan = parse_ensemble_plan(response)
        
        assert len(plan.implementation_steps) >= 3
        assert any("load" in step.lower() for step in plan.implementation_steps)
        assert any("average" in step.lower() for step in plan.implementation_steps)
    
    def test_select_best_ensemble_returns_highest_score(self):
        """Test that select_best_ensemble returns the attempt with highest score."""
        attempts = [
            EnsembleResult(
                strategy="Simple Average",
                merged_code="code_a",
                validation_score=0.82,
                iteration=1,
            ),
            EnsembleResult(
                strategy="Weighted Average",
                merged_code="code_b",
                validation_score=0.88,
                iteration=2,
            ),
            EnsembleResult(
                strategy="Stacking",
                merged_code="code_c",
                validation_score=0.85,
                iteration=3,
            ),
        ]
        
        best = select_best_ensemble(attempts)
        
        assert best.strategy == "Weighted Average"
        assert best.validation_score == pytest.approx(0.88)
        assert best.iteration == 2
    
    def test_select_best_ensemble_empty_list(self):
        """Test select_best_ensemble with empty list returns default result."""
        best = select_best_ensemble([])
        
        assert best.strategy == "No attempts"
        assert best.validation_score == float("-inf")
    
    def test_is_strategy_similar_to_previous_detects_similarity(self):
        """Test that similar strategies are detected."""
        new_plan = EnsemblePlan(
            strategy_name="Weighted Average Ensemble",
            description="Use weighted averaging based on validation scores",
            implementation_steps=["Train models", "Average predictions weighted by scores"],
            weight_assignment="Based on validation scores",
            expected_benefit="Better performance through weighted combination",
            success=True,
        )
        
        previous_attempts = [
            EnsembleResult(
                strategy="Weighted Average Ensemble based on validation scores",
                merged_code="code",
                validation_score=0.8,
                iteration=1,
            ),
        ]
        
        # Should detect similarity with low threshold
        assert is_strategy_similar_to_previous(new_plan, previous_attempts, similarity_threshold=0.2)
    
    def test_is_strategy_similar_to_previous_allows_different(self):
        """Test that different strategies are allowed."""
        new_plan = EnsemblePlan(
            strategy_name="Stacking with Meta-Learner",
            description="Use stacking approach",
            implementation_steps=["Train base models", "Train meta-learner"],
            weight_assignment=None,
            expected_benefit="Better performance",
            success=True,
        )
        
        previous_attempts = [
            EnsembleResult(
                strategy="Simple Average",
                merged_code="code",
                validation_score=0.8,
                iteration=1,
            ),
        ]
        
        # Should allow different strategy
        assert not is_strategy_similar_to_previous(new_plan, previous_attempts, similarity_threshold=0.8)


class TestEnsembleGraphStructure:
    """Test the EnsembleGraph structure and configuration."""
    
    def test_graph_has_all_required_nodes(self):
        """Test that the graph contains all required nodes."""
        config = MLEStarConfig()
        graph = EnsembleGraph(config)
        
        required_nodes = ["ensemble_planner", "ensembler"]
        for node in required_nodes:
            assert node in graph._nodes, f"Missing node: {node}"
    
    def test_graph_has_iterative_edge(self):
        """Test that graph has conditional edge for iteration."""
        config = MLEStarConfig()
        graph = EnsembleGraph(config)
        
        # Find the edge from ensembler back to planner
        iterative_edge = None
        for source, target, condition in graph._edges:
            if source == "ensembler" and target == "ensemble_planner":
                iterative_edge = (source, target, condition)
                break
        
        assert iterative_edge is not None, "Missing iterative edge"
        assert iterative_edge[2] is not None, "Iterative edge should have a condition"
    
    def test_graph_entry_point_is_ensemble_planner(self):
        """Test that the entry point is the ensemble_planner node."""
        config = MLEStarConfig()
        graph = EnsembleGraph(config)
        
        assert graph._entry_point == "ensemble_planner"
    
    def test_should_continue_iteration_respects_max_iterations(self):
        """Test that iteration condition respects max iterations."""
        config = MLEStarConfig(ensemble_iterations=5)
        graph = EnsembleGraph(config)
        
        task = TaskDescription(
            description="Test",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Should continue when under max iterations
        state = EnsembleState(
            task=task,
            config=config,
            solutions=[("code1", 0.8), ("code2", 0.82)],
            iteration=3,
        )
        assert graph._should_continue_iteration(state) is True
        
        # Should stop when at max iterations
        state.iteration = 5
        assert graph._should_continue_iteration(state) is False
        
        # Should stop when error occurs
        state.iteration = 3
        state.error = "Some error"
        assert graph._should_continue_iteration(state) is False


class TestEnsembleState:
    """Test EnsembleState initialization and updates."""
    
    def test_state_initialization(self):
        """Test that state initializes with correct defaults."""
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        config = MLEStarConfig()
        
        state = EnsembleState(
            task=task,
            config=config,
            solutions=[("code1", 0.8), ("code2", 0.82)],
        )
        
        assert state.task == task
        assert state.config == config
        assert len(state.solutions) == 2
        assert state.current_plan is None
        assert state.current_result is None
        assert state.attempts == []
        assert state.best_result is None
        assert state.iteration == 0
        assert state.completed is False
        assert state.error is None


class TestPhase3Integration:
    """Integration tests for the complete Phase 3 flow."""
    
    def test_graph_handles_single_solution(self):
        """Test that graph handles single solution without ensemble."""
        import asyncio
        
        config = MLEStarConfig()
        graph = EnsembleGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        solutions = [("print('single')", 0.85)]
        
        state = asyncio.run(graph.run(task=task, solutions=solutions))
        
        assert state.error is None
        assert state.completed
        assert state.best_result is not None
        assert state.best_result.validation_score == pytest.approx(0.85)
        assert "single" in state.best_result.strategy.lower()
    
    def test_graph_handles_empty_solutions(self):
        """Test that graph handles empty solutions list."""
        import asyncio
        
        config = MLEStarConfig()
        graph = EnsembleGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        state = asyncio.run(graph.run(task=task, solutions=[]))
        
        assert state.error is not None
        assert "No solutions" in state.error
        assert state.completed
    
    def test_graph_stops_on_planner_error(self):
        """Test that graph stops execution when planner fails."""
        import asyncio
        
        config = MLEStarConfig()
        graph = EnsembleGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock the planner to fail
        async def mock_planner_node(state):
            state.error = "Planner failed: Could not propose strategy"
            return state
        
        graph._nodes["ensemble_planner"] = mock_planner_node
        
        solutions = [("code1", 0.8), ("code2", 0.82)]
        state = asyncio.run(graph.run(task=task, solutions=solutions))
        
        assert state.error is not None
        assert "Planner failed" in state.error
    
    def test_graph_completes_one_iteration_with_mocked_nodes(self):
        """Test that graph completes one iteration with mocked nodes."""
        import asyncio
        
        config = MLEStarConfig(ensemble_iterations=1)
        graph = EnsembleGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock all nodes to succeed
        async def mock_planner(state):
            state.current_plan = EnsemblePlan(
                strategy_name="Weighted Average",
                description="Use weighted averaging",
                implementation_steps=["Train", "Average", "Evaluate"],
                weight_assignment="Based on scores",
                expected_benefit="Better performance",
                success=True,
            )
            return state
        
        async def mock_ensembler(state):
            state.current_result = EnsembleImplementationResult(
                merged_code="print('ensemble')",
                validation_score=0.88,
                strategy_name="Weighted Average",
                success=True,
            )
            
            ensemble_result = EnsembleResult(
                strategy="Weighted Average",
                merged_code="print('ensemble')",
                validation_score=0.88,
                iteration=state.iteration + 1,
            )
            state.attempts.append(ensemble_result)
            state.best_result = ensemble_result
            state.iteration += 1
            return state
        
        graph._nodes["ensemble_planner"] = mock_planner
        graph._nodes["ensembler"] = mock_ensembler
        
        solutions = [("code1", 0.8), ("code2", 0.82)]
        state = asyncio.run(graph.run(task=task, solutions=solutions))
        
        assert state.error is None
        assert state.completed
        assert state.iteration == 1
        assert state.best_result is not None
        assert state.best_result.validation_score == pytest.approx(0.88)
        assert state.best_result.strategy == "Weighted Average"
    
    def test_graph_selects_best_from_multiple_iterations(self):
        """Test that graph selects best result from multiple iterations."""
        import asyncio
        
        config = MLEStarConfig(ensemble_iterations=3)
        graph = EnsembleGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Track iteration for varying scores
        iteration_scores = [0.82, 0.88, 0.85]  # Second iteration is best
        
        async def mock_planner(state):
            state.current_plan = EnsemblePlan(
                strategy_name=f"Strategy {state.iteration + 1}",
                description="Test strategy",
                implementation_steps=["Step 1"],
                weight_assignment=None,
                expected_benefit="Better",
                success=True,
            )
            return state
        
        async def mock_ensembler(state):
            score = iteration_scores[state.iteration] if state.iteration < len(iteration_scores) else 0.8
            
            ensemble_result = EnsembleResult(
                strategy=f"Strategy {state.iteration + 1}",
                merged_code=f"code_{state.iteration}",
                validation_score=score,
                iteration=state.iteration + 1,
            )
            state.attempts.append(ensemble_result)
            
            # Update best if this is better
            if state.best_result is None or score > state.best_result.validation_score:
                state.best_result = ensemble_result
            
            state.iteration += 1
            return state
        
        graph._nodes["ensemble_planner"] = mock_planner
        graph._nodes["ensembler"] = mock_ensembler
        
        solutions = [("code1", 0.8), ("code2", 0.82)]
        state = asyncio.run(graph.run(task=task, solutions=solutions))
        
        assert state.error is None
        assert state.completed
        assert state.iteration == 3
        assert len(state.attempts) == 3
        # Best result should be from iteration 2 (score 0.88)
        assert state.best_result is not None
        assert state.best_result.validation_score == pytest.approx(0.88)
        assert state.best_result.strategy == "Strategy 2"
