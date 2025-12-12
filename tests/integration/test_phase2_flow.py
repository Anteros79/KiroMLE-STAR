"""Integration tests for Phase 2: Iterative Refinement flow.

Tests the ablation → summarize → extract → refine loop.
Requirements: 5.1, 6.1, 7.1
"""

import pytest

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import (
    TaskDescription,
    SolutionState,
    RefinementAttempt,
)
from mle_star.graphs.refinement import (
    RefinementGraph,
    RefinementState,
    RefinementLoopNode,
)
from mle_star.agents.ablation_study import parse_ablation_results, AblationResult
from mle_star.agents.summarizer import parse_ablation_summary, AblationSummary
from mle_star.agents.extractor import ExtractedBlock
from mle_star.tools.refinement_utils import select_best_attempt, InnerLoopResult


class TestPhase2Components:
    """Test individual Phase 2 components work correctly."""
    
    def test_parse_ablation_results_with_impacts(self):
        """Test parsing ablation results with component impacts."""
        response = """
Ablation Results:
- Baseline: 0.8500
- Without feature_engineering: 0.7800 (impact: 0.0700)
- Without model_tuning: 0.8200 (impact: 0.0300)
- Without preprocessing: 0.8100 (impact: 0.0400)
"""
        baseline, impacts = parse_ablation_results(response)
        
        assert baseline == pytest.approx(0.85)
        assert len(impacts) == 3
        assert impacts["feature_engineering"] == pytest.approx(0.07)
        assert impacts["model_tuning"] == pytest.approx(0.03)
        assert impacts["preprocessing"] == pytest.approx(0.04)
    
    def test_parse_ablation_results_without_explicit_impact(self):
        """Test parsing ablation results when impact is calculated from scores."""
        response = """
Ablation Results:
- Baseline: 0.9000
- Without normalization: 0.8500
- Without feature_selection: 0.8700
"""
        baseline, impacts = parse_ablation_results(response)
        
        assert baseline == pytest.approx(0.90)
        assert len(impacts) == 2
        # Impact should be baseline - score
        assert impacts["normalization"] == pytest.approx(0.05)
        assert impacts["feature_selection"] == pytest.approx(0.03)
    
    def test_parse_ablation_summary_identifies_most_impactful(self):
        """Test that summary parsing identifies the most impactful component."""
        response = """
## Ablation Summary

### Baseline Performance
- Score: 0.8500

### Component Impacts (sorted by impact)
1. feature_engineering: Impact = 0.0700 (removing this decreases performance)
2. preprocessing: Impact = 0.0400 (removing this decreases performance)
3. model_tuning: Impact = 0.0300 (removing this decreases performance)

### Most Impactful Component
- Component: feature_engineering
- Impact: 0.0700
- Recommendation: Consider improving this component

### Key Insights
- Feature engineering has the largest impact
- All components contribute positively
"""
        summary = parse_ablation_summary(response)
        
        assert summary.success
        assert summary.baseline_score == pytest.approx(0.85)
        assert summary.most_impactful_component == "feature_engineering"
        assert summary.most_impactful_delta == pytest.approx(0.07)
        assert len(summary.insights) >= 1
    
    def test_select_best_attempt_returns_highest_score(self):
        """Test that select_best_attempt returns the attempt with highest score."""
        attempts = [
            RefinementAttempt(
                plan="Plan A",
                refined_code_block="code_a",
                full_solution="solution_a",
                validation_score=0.82,
                iteration=0,
            ),
            RefinementAttempt(
                plan="Plan B",
                refined_code_block="code_b",
                full_solution="solution_b",
                validation_score=0.88,
                iteration=1,
            ),
            RefinementAttempt(
                plan="Plan C",
                refined_code_block="code_c",
                full_solution="solution_c",
                validation_score=0.85,
                iteration=2,
            ),
        ]
        
        initial_score = 0.80
        result = select_best_attempt(attempts, initial_score)
        
        assert result.best_attempt is not None
        assert result.best_attempt.plan == "Plan B"
        assert result.best_score == pytest.approx(0.88)
        assert result.improved
    
    def test_select_best_attempt_no_improvement(self):
        """Test select_best_attempt when no attempt improves on initial score."""
        attempts = [
            RefinementAttempt(
                plan="Plan A",
                refined_code_block="code_a",
                full_solution="solution_a",
                validation_score=0.75,
                iteration=0,
            ),
            RefinementAttempt(
                plan="Plan B",
                refined_code_block="code_b",
                full_solution="solution_b",
                validation_score=0.78,
                iteration=1,
            ),
        ]
        
        initial_score = 0.85
        result = select_best_attempt(attempts, initial_score)
        
        # Should still return the best attempt, but improved should be False
        assert result.best_attempt is not None
        assert result.best_score == pytest.approx(0.78)
        assert not result.improved


class TestRefinementGraphStructure:
    """Test the RefinementGraph structure and configuration."""
    
    def test_graph_has_all_required_nodes(self):
        """Test that the graph contains all required nodes."""
        config = MLEStarConfig()
        graph = RefinementGraph(config)
        
        required_nodes = ["ablation", "summarize", "extract", "refine"]
        for node in required_nodes:
            assert node in graph._nodes, f"Missing node: {node}"
    
    def test_graph_has_cyclic_edge_for_outer_loop(self):
        """Test that graph has conditional edge back to ablation for outer loop."""
        config = MLEStarConfig()
        graph = RefinementGraph(config)
        
        # Find the edge from refine back to ablation
        cyclic_edge = None
        for source, target, condition in graph._edges:
            if source == "refine" and target == "ablation":
                cyclic_edge = (source, target, condition)
                break
        
        assert cyclic_edge is not None, "Missing cyclic edge from refine to ablation"
        assert cyclic_edge[2] is not None, "Cyclic edge should have a condition"
    
    def test_graph_entry_point_is_ablation(self):
        """Test that the entry point is the ablation node."""
        config = MLEStarConfig()
        graph = RefinementGraph(config)
        
        assert graph._entry_point == "ablation"
    
    def test_should_continue_outer_loop_respects_max_iterations(self):
        """Test that outer loop condition respects max iterations."""
        config = MLEStarConfig(outer_loop_iterations=4)
        graph = RefinementGraph(config)
        
        task = TaskDescription(
            description="Test",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        solution_state = SolutionState(
            current_code="pass",
            validation_score=0.8,
        )
        
        # Should continue when under max iterations
        state = RefinementState(
            task=task,
            config=config,
            solution_state=solution_state,
            outer_iteration=2,
        )
        assert graph._should_continue_outer_loop(state) is True
        
        # Should stop when at max iterations
        state.outer_iteration = 4
        assert graph._should_continue_outer_loop(state) is False
        
        # Should stop when error occurs
        state.outer_iteration = 2
        state.error = "Some error"
        assert graph._should_continue_outer_loop(state) is False


class TestRefinementState:
    """Test RefinementState initialization and updates."""
    
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
        solution_state = SolutionState(
            current_code="print('test')",
            validation_score=0.8,
        )
        
        state = RefinementState(
            task=task,
            config=config,
            solution_state=solution_state,
        )
        
        assert state.task == task
        assert state.config == config
        assert state.solution_state == solution_state
        assert state.ablation_result is None
        assert state.ablation_summary is None
        assert state.extracted_block is None
        assert state.inner_loop_result is None
        assert state.outer_iteration == 0
        assert state.completed is False
        assert state.error is None


class TestRefinementLoopNode:
    """Test the RefinementLoopNode inner loop logic."""
    
    def test_loop_node_initialization(self):
        """Test that loop node initializes with config."""
        config = MLEStarConfig(inner_loop_iterations=3)
        node = RefinementLoopNode(config)
        
        assert node.config.inner_loop_iterations == 3


class TestPhase2Integration:
    """Integration tests for the complete Phase 2 flow."""
    
    def test_graph_stops_on_ablation_error(self):
        """Test that graph stops execution when ablation fails."""
        import asyncio
        
        config = MLEStarConfig()
        graph = RefinementGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock the ablation node to fail
        async def mock_ablation_node(state):
            state.error = "Ablation failed: Code execution error"
            return state
        
        graph._nodes["ablation"] = mock_ablation_node
        
        state = asyncio.run(graph.run(
            task=task,
            initial_solution="print('test')",
            initial_score=0.8,
        ))
        
        assert state.error is not None
        assert "Ablation failed" in state.error
        assert state.ablation_summary is None
    
    def test_graph_stops_on_summarize_error(self):
        """Test that graph stops execution when summarization fails."""
        import asyncio
        
        config = MLEStarConfig()
        graph = RefinementGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock ablation to succeed
        async def mock_ablation_node(state):
            state.ablation_result = AblationResult(
                baseline_score=0.8,
                component_impacts={"feature_eng": 0.05},
                raw_output="test output",
                success=True,
            )
            return state
        
        # Mock summarize to fail
        async def mock_summarize_node(state):
            state.error = "Summarization failed: Could not parse output"
            return state
        
        graph._nodes["ablation"] = mock_ablation_node
        graph._nodes["summarize"] = mock_summarize_node
        
        state = asyncio.run(graph.run(
            task=task,
            initial_solution="print('test')",
            initial_score=0.8,
        ))
        
        assert state.error is not None
        assert "Summarization failed" in state.error
        assert state.ablation_result is not None  # Ablation succeeded
    
    def test_graph_completes_one_iteration_with_mocked_nodes(self):
        """Test that graph completes one outer iteration with mocked nodes."""
        import asyncio
        
        config = MLEStarConfig(outer_loop_iterations=1)
        graph = RefinementGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock all nodes to succeed
        async def mock_ablation(state):
            state.ablation_result = AblationResult(
                baseline_score=0.8,
                component_impacts={"feature_eng": 0.05},
                raw_output="test output",
                success=True,
            )
            return state
        
        async def mock_summarize(state):
            state.ablation_summary = AblationSummary(
                baseline_score=0.8,
                component_impacts={"feature_eng": 0.05},
                most_impactful_component="feature_eng",
                most_impactful_delta=0.05,
                insights=["Feature engineering is important"],
                raw_summary="test summary",
                success=True,
            )
            state.solution_state.ablation_summaries.append("test summary")
            return state
        
        async def mock_extract(state):
            state.extracted_block = ExtractedBlock(
                component_name="feature_eng",
                code_block="def feature_eng(): pass",
                impact=0.05,
                refinement_plan="Improve feature engineering",
                expected_improvement=0.02,
                success=True,
            )
            return state
        
        async def mock_refine(state):
            state.inner_loop_result = InnerLoopResult(
                best_attempt=RefinementAttempt(
                    plan="Improve feature engineering",
                    refined_code_block="def feature_eng(): return X",
                    full_solution="print('improved')",
                    validation_score=0.85,
                    iteration=0,
                ),
                best_score=0.85,
                all_attempts=[],
                improved=True,
            )
            state.solution_state.current_code = "print('improved')"
            state.solution_state.validation_score = 0.85
            state.outer_iteration += 1
            return state
        
        graph._nodes["ablation"] = mock_ablation
        graph._nodes["summarize"] = mock_summarize
        graph._nodes["extract"] = mock_extract
        graph._nodes["refine"] = mock_refine
        
        state = asyncio.run(graph.run(
            task=task,
            initial_solution="print('test')",
            initial_score=0.8,
        ))
        
        assert state.error is None
        assert state.completed
        assert state.outer_iteration == 1
        assert state.solution_state.validation_score == pytest.approx(0.85)
