"""Integration tests for Phase 1: Initial Solution Generation flow.

Tests the retriever → evaluator → merger pipeline.
Requirements: 2.1, 3.1, 4.1
"""

import pytest

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import TaskDescription, ModelCandidate
from mle_star.graphs.initial_solution import (
    InitialSolutionGraph,
    InitialSolutionState,
)
from mle_star.agents.retriever import (
    parse_model_candidates_from_response,
    _extract_model_name,
    _extract_description,
    _extract_code_example,
)
from mle_star.agents.candidate_evaluator import (
    sort_candidates_by_score,
    _extract_score_from_response,
)
from mle_star.agents.merger import MergeResult


class TestPhase1Components:
    """Test individual Phase 1 components work correctly."""
    
    def test_parse_model_candidates_from_structured_response(self):
        """Test parsing model candidates from a well-structured response."""
        response = """
## Model 1: RandomForest

**Description:** Random Forest is an ensemble method that works well for tabular data.

```python
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)
```

## Model 2: XGBoost

**Description:** XGBoost is a gradient boosting library optimized for speed.

```python
import xgboost as xgb
model = xgb.XGBClassifier()
model.fit(X_train, y_train)
```
"""
        candidates = parse_model_candidates_from_response(response)
        
        # Should extract at least one candidate
        assert len(candidates) >= 1
        
        # Each candidate should have required fields
        for candidate in candidates:
            assert candidate.name
            assert candidate.description
    
    def test_extract_model_name_from_various_formats(self):
        """Test model name extraction from different text formats."""
        # Test markdown header format
        text1 = "## RandomForest\nA great model"
        assert _extract_model_name(text1) != ""
        
        # Test bold format
        text2 = "**XGBoost** is a gradient boosting library"
        assert _extract_model_name(text2) != ""
        
        # Test numbered list format
        text3 = "1. LightGBM\nFast gradient boosting"
        assert _extract_model_name(text3) != ""
    
    def test_extract_code_example_from_code_block(self):
        """Test code extraction from markdown code blocks."""
        text = """
Some description here.

```python
import pandas as pd
df = pd.read_csv('data.csv')
model.fit(df)
```

More text after.
"""
        code = _extract_code_example(text)
        assert code
        assert "import pandas" in code
        assert "model.fit" in code
    
    def test_sort_candidates_by_score_descending(self):
        """Test that candidates are sorted by score in descending order."""
        candidates = [
            ModelCandidate(name="A", description="", example_code="", validation_score=0.7),
            ModelCandidate(name="B", description="", example_code="", validation_score=0.9),
            ModelCandidate(name="C", description="", example_code="", validation_score=0.8),
            ModelCandidate(name="D", description="", example_code="", validation_score=None),
        ]
        
        sorted_candidates = sort_candidates_by_score(candidates)
        
        # Best score should be first
        assert sorted_candidates[0].name == "B"
        assert sorted_candidates[1].name == "C"
        assert sorted_candidates[2].name == "A"
        # None scores should be at the end
        assert sorted_candidates[3].name == "D"
    
    def test_extract_validation_score_from_response(self):
        """Test extraction of validation score from various response formats."""
        # Standard format
        response1 = "Final Validation Performance: 0.8523"
        assert _extract_score_from_response(response1) == pytest.approx(0.8523)
        
        # Alternative format
        response2 = "Validation Score: 0.91"
        assert _extract_score_from_response(response2) == pytest.approx(0.91)
        
        # Parsed format from tool output
        response3 = "Parsed Validation Score: 0.7654"
        assert _extract_score_from_response(response3) == pytest.approx(0.7654)


class TestInitialSolutionGraphStructure:
    """Test the InitialSolutionGraph structure and configuration."""
    
    def test_graph_has_all_required_nodes(self):
        """Test that the graph contains all required nodes."""
        config = MLEStarConfig()
        graph = InitialSolutionGraph(config)
        
        required_nodes = ["retriever", "evaluator", "merger", "leakage_check", "usage_check"]
        for node in required_nodes:
            assert node in graph._nodes, f"Missing node: {node}"
    
    def test_graph_has_correct_edge_sequence(self):
        """Test that edges define the correct sequential flow."""
        config = MLEStarConfig()
        graph = InitialSolutionGraph(config)
        
        expected_edges = [
            ("retriever", "evaluator"),
            ("evaluator", "merger"),
            ("merger", "leakage_check"),
            ("leakage_check", "usage_check"),
        ]
        
        assert graph._edges == expected_edges
    
    def test_graph_entry_point_is_retriever(self):
        """Test that the entry point is the retriever node."""
        config = MLEStarConfig()
        graph = InitialSolutionGraph(config)
        
        assert graph._entry_point == "retriever"


class TestInitialSolutionState:
    """Test InitialSolutionState initialization and updates."""
    
    def test_state_initialization(self):
        """Test that state initializes with correct defaults."""
        task = TaskDescription(
            description="Test classification task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        config = MLEStarConfig()
        
        state = InitialSolutionState(task=task, config=config)
        
        assert state.task == task
        assert state.config == config
        assert state.candidates == []
        assert state.evaluated_candidates == []
        assert state.merge_result is None
        assert state.leakage_result is None
        assert state.usage_result is None
        assert state.final_solution == ""
        assert state.final_score is None
        assert state.error is None


class TestMergeResult:
    """Test MergeResult dataclass."""
    
    def test_merge_result_success(self):
        """Test successful merge result creation."""
        result = MergeResult(
            merged_code="print('merged')",
            validation_score=0.85,
            models_included=["ModelA", "ModelB"],
            success=True,
        )
        
        assert result.success
        assert result.validation_score == 0.85
        assert len(result.models_included) == 2
        assert result.error_message is None
    
    def test_merge_result_failure(self):
        """Test failed merge result creation."""
        result = MergeResult(
            merged_code="",
            validation_score=None,
            models_included=[],
            success=False,
            error_message="Merge failed",
        )
        
        assert not result.success
        assert result.validation_score is None
        assert result.error_message == "Merge failed"


class TestPhase1Integration:
    """Integration tests for the complete Phase 1 flow."""
    
    def test_graph_stops_on_retriever_error(self):
        """Test that graph stops execution when retriever fails."""
        import asyncio
        
        config = MLEStarConfig()
        graph = InitialSolutionGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/nonexistent/path.csv",
        )
        
        # Mock the retriever to fail
        async def mock_retriever_node(state):
            state.error = "Retriever failed: No models found"
            return state
        
        graph._nodes["retriever"] = mock_retriever_node
        
        state = asyncio.run(graph.run(task))
        
        assert state.error is not None
        assert "Retriever failed" in state.error
        # Subsequent nodes should not have been executed
        assert state.evaluated_candidates == []
        assert state.merge_result is None
    
    def test_graph_stops_on_evaluator_error(self):
        """Test that graph stops execution when evaluator fails."""
        import asyncio
        
        config = MLEStarConfig()
        graph = InitialSolutionGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock retriever to succeed
        async def mock_retriever_node(state):
            state.candidates = [
                ModelCandidate(name="TestModel", description="Test", example_code="pass")
            ]
            return state
        
        # Mock evaluator to fail
        async def mock_evaluator_node(state):
            state.error = "Evaluator failed: Code execution error"
            return state
        
        graph._nodes["retriever"] = mock_retriever_node
        graph._nodes["evaluator"] = mock_evaluator_node
        
        state = asyncio.run(graph.run(task))
        
        assert state.error is not None
        assert "Evaluator failed" in state.error
        assert len(state.candidates) == 1  # Retriever succeeded
        assert state.merge_result is None  # Merger not reached
    
    def test_graph_completes_successfully_with_mocked_nodes(self):
        """Test that graph completes when all nodes succeed."""
        import asyncio
        
        config = MLEStarConfig()
        graph = InitialSolutionGraph(config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock all nodes to succeed
        async def mock_retriever(state):
            state.candidates = [
                ModelCandidate(name="Model1", description="Test", example_code="pass", validation_score=0.8)
            ]
            return state
        
        async def mock_evaluator(state):
            state.evaluated_candidates = state.candidates
            return state
        
        async def mock_merger(state):
            state.merge_result = MergeResult(
                merged_code="print('solution')",
                validation_score=0.85,
                models_included=["Model1"],
                success=True,
            )
            state.final_solution = "print('solution')"
            state.final_score = 0.85
            return state
        
        async def mock_leakage_check(state):
            return state
        
        async def mock_usage_check(state):
            return state
        
        graph._nodes["retriever"] = mock_retriever
        graph._nodes["evaluator"] = mock_evaluator
        graph._nodes["merger"] = mock_merger
        graph._nodes["leakage_check"] = mock_leakage_check
        graph._nodes["usage_check"] = mock_usage_check
        
        state = asyncio.run(graph.run(task))
        
        assert state.error is None
        assert state.final_solution == "print('solution')"
        assert state.final_score == 0.85
