"""Unit tests for MLEStarOrchestrator."""

import pytest
from mle_star.orchestrator import (
    MLEStarOrchestrator,
    OrchestratorState,
    create_orchestrator,
)
from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import TaskDescription


class TestMLEStarOrchestratorInit:
    """Tests for MLEStarOrchestrator initialization."""
    
    def test_init_with_default_config(self):
        """Test orchestrator initializes with default config."""
        orchestrator = MLEStarOrchestrator()
        
        assert orchestrator.config is not None
        assert orchestrator.config.num_retrieved_models == 4
        assert orchestrator.config.inner_loop_iterations == 4
        assert orchestrator.config.outer_loop_iterations == 4
        assert orchestrator.config.ensemble_iterations == 5
        assert orchestrator.parallel_runs == MLEStarOrchestrator.DEFAULT_PARALLEL_RUNS
    
    def test_init_with_custom_config(self):
        """Test orchestrator initializes with custom config."""
        config = MLEStarConfig(
            num_retrieved_models=2,
            inner_loop_iterations=2,
            outer_loop_iterations=2,
            ensemble_iterations=3,
        )
        orchestrator = MLEStarOrchestrator(config=config)
        
        assert orchestrator.config.num_retrieved_models == 2
        assert orchestrator.config.inner_loop_iterations == 2
        assert orchestrator.config.outer_loop_iterations == 2
        assert orchestrator.config.ensemble_iterations == 3
    
    def test_init_with_custom_parallel_runs(self):
        """Test orchestrator initializes with custom parallel runs."""
        orchestrator = MLEStarOrchestrator(parallel_runs=5)
        
        assert orchestrator.parallel_runs == 5
    
    def test_state_is_none_before_run(self):
        """Test state is None before running the pipeline."""
        orchestrator = MLEStarOrchestrator()
        
        assert orchestrator.state is None


class TestCreateOrchestrator:
    """Tests for create_orchestrator factory function."""
    
    def test_create_with_defaults(self):
        """Test factory creates orchestrator with defaults."""
        orchestrator = create_orchestrator()
        
        assert isinstance(orchestrator, MLEStarOrchestrator)
        assert orchestrator.config is not None
    
    def test_create_with_config(self):
        """Test factory creates orchestrator with custom config."""
        config = MLEStarConfig(num_retrieved_models=3)
        orchestrator = create_orchestrator(config=config)
        
        assert orchestrator.config.num_retrieved_models == 3
    
    def test_create_with_parallel_runs(self):
        """Test factory creates orchestrator with custom parallel runs."""
        orchestrator = create_orchestrator(parallel_runs=4)
        
        assert orchestrator.parallel_runs == 4


class TestOrchestratorState:
    """Tests for OrchestratorState dataclass."""
    
    def test_state_initialization(self):
        """Test OrchestratorState initializes correctly."""
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        config = MLEStarConfig()
        
        state = OrchestratorState(task=task, config=config)
        
        assert state.task == task
        assert state.config == config
        assert state.phase1_state is None
        assert state.phase2_states == []
        assert state.phase3_state is None
        assert state.submission_result is None
        assert state.final_solution == ""
        assert state.final_score is None
        assert state.current_phase == 0
        assert state.error is None
        assert state.completed is False


class TestCheckpointMethods:
    """Tests for checkpoint creation and recovery."""
    
    def test_create_checkpoint_empty_state(self):
        """Test checkpoint creation with empty state."""
        orchestrator = MLEStarOrchestrator()
        
        # State is None, should return empty dict
        checkpoint = orchestrator._create_checkpoint(1)
        
        assert checkpoint == {}
    
    def test_recover_from_checkpoint_basic(self):
        """Test basic checkpoint recovery."""
        orchestrator = MLEStarOrchestrator()
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        checkpoint = {
            "phase": 2,
            "task_description": "Test task",
            "config": orchestrator.config.to_dict(),
            "phase1_solution": "print('hello')",
            "phase1_score": 0.85,
        }
        
        phase = orchestrator._recover_from_checkpoint(checkpoint, task)
        
        assert phase == 2
        assert orchestrator._state is not None
        assert orchestrator._state.phase1_state is not None
        assert orchestrator._state.phase1_state.final_solution == "print('hello')"
        assert orchestrator._state.phase1_state.final_score == 0.85
