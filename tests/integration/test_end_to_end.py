"""End-to-end integration tests for the full MLE-STAR pipeline.

Tests the full pipeline on a simple classification task.
Requirements: 1.1, 13.3
"""

import pytest

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import (
    TaskDescription,
    ModelCandidate,
    SolutionState,
    EnsembleResult,
)
from mle_star.orchestrator import (
    MLEStarOrchestrator,
    OrchestratorState,
    create_orchestrator,
)
from mle_star.graphs.initial_solution import InitialSolutionState
from mle_star.graphs.refinement import RefinementState
from mle_star.graphs.ensemble import EnsembleState
from mle_star.agents.merger import MergeResult
from mle_star.agents.submission import SubmissionResult


class TestOrchestratorConfiguration:
    """Test orchestrator configuration and initialization."""
    
    def test_orchestrator_accepts_custom_config(self):
        """Test that orchestrator accepts custom configuration."""
        config = MLEStarConfig(
            num_retrieved_models=2,
            inner_loop_iterations=2,
            outer_loop_iterations=2,
            ensemble_iterations=3,
            max_debug_retries=2,
        )
        
        orchestrator = MLEStarOrchestrator(config=config)
        
        assert orchestrator.config.num_retrieved_models == 2
        assert orchestrator.config.inner_loop_iterations == 2
        assert orchestrator.config.outer_loop_iterations == 2
        assert orchestrator.config.ensemble_iterations == 3
        assert orchestrator.config.max_debug_retries == 2
    
    def test_orchestrator_factory_function(self):
        """Test the create_orchestrator factory function."""
        config = MLEStarConfig(num_retrieved_models=3)
        orchestrator = create_orchestrator(config=config, parallel_runs=2)
        
        assert isinstance(orchestrator, MLEStarOrchestrator)
        assert orchestrator.config.num_retrieved_models == 3
        assert orchestrator.parallel_runs == 2
    
    def test_orchestrator_state_is_none_before_run(self):
        """Test that state is None before running."""
        orchestrator = MLEStarOrchestrator()
        
        assert orchestrator.state is None


class TestTaskDescriptionParsing:
    """Test TaskDescription parsing from text."""
    
    def test_parse_classification_task(self):
        """Test parsing a classification task description."""
        text = """
        This is a binary classification task on tabular data.
        The goal is to predict customer churn.
        Evaluation metric: AUC-ROC
        Dataset: /data/churn.csv
        """
        
        task = TaskDescription.parse_from_text(text)
        
        assert task.task_type == "binary_classification"
        assert task.data_modality == "tabular"
        assert task.evaluation_metric == "auc_roc"
    
    def test_parse_regression_task(self):
        """Test parsing a regression task description."""
        text = """
        Predict house prices using regression on tabular data.
        Evaluation metric: RMSE
        Dataset path: /data/housing.csv
        """
        
        task = TaskDescription.parse_from_text(text)
        
        assert task.task_type == "regression"
        assert task.data_modality == "tabular"
        assert task.evaluation_metric == "rmse"
    
    def test_parse_image_classification_task(self):
        """Test parsing an image classification task."""
        text = """
        Multi-class classification of images.
        Evaluation metric: accuracy
        Dataset: /data/images/
        """
        
        task = TaskDescription.parse_from_text(text)
        
        assert task.task_type == "multiclass_classification"
        assert task.data_modality == "image"
        assert task.evaluation_metric == "accuracy"


class TestCheckpointRecovery:
    """Test checkpoint creation and recovery."""
    
    def test_checkpoint_creation_with_phase1_state(self):
        """Test checkpoint creation after Phase 1."""
        orchestrator = MLEStarOrchestrator()
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Manually set up state as if Phase 1 completed
        orchestrator._state = OrchestratorState(
            task=task,
            config=orchestrator.config,
        )
        orchestrator._state.phase1_state = InitialSolutionState(
            task=task,
            config=orchestrator.config,
            final_solution="print('solution')",
            final_score=0.85,
        )
        
        checkpoint = orchestrator._create_checkpoint(1)
        
        assert checkpoint["phase"] == 1
        assert checkpoint["phase1_solution"] == "print('solution')"
        assert checkpoint["phase1_score"] == 0.85
    
    def test_checkpoint_recovery_restores_phase1_state(self):
        """Test that checkpoint recovery restores Phase 1 state."""
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
            "phase1_solution": "print('recovered')",
            "phase1_score": 0.82,
        }
        
        phase = orchestrator._recover_from_checkpoint(checkpoint, task)
        
        assert phase == 2
        assert orchestrator._state is not None
        assert orchestrator._state.phase1_state is not None
        assert orchestrator._state.phase1_state.final_solution == "print('recovered')"
        assert orchestrator._state.phase1_state.final_score == 0.82


class TestEndToEndWithMockedPipeline:
    """End-to-end tests with mocked pipeline components."""
    
    def test_full_pipeline_with_mocked_graphs(self):
        """Test full pipeline execution with mocked graph components."""
        import asyncio
        
        config = MLEStarConfig(
            num_retrieved_models=2,
            inner_loop_iterations=1,
            outer_loop_iterations=1,
            ensemble_iterations=1,
        )
        orchestrator = MLEStarOrchestrator(config=config, parallel_runs=2)
        
        task = TaskDescription(
            description="Binary classification on tabular data with accuracy metric",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock Phase 1 graph
        async def mock_phase1_run(task_input):
            return InitialSolutionState(
                task=task_input,
                config=config,
                candidates=[
                    ModelCandidate(name="RF", description="Random Forest", example_code="pass", validation_score=0.82),
                    ModelCandidate(name="XGB", description="XGBoost", example_code="pass", validation_score=0.85),
                ],
                evaluated_candidates=[
                    ModelCandidate(name="XGB", description="XGBoost", example_code="pass", validation_score=0.85),
                    ModelCandidate(name="RF", description="Random Forest", example_code="pass", validation_score=0.82),
                ],
                merge_result=MergeResult(
                    merged_code="print('merged')",
                    validation_score=0.87,
                    models_included=["XGB", "RF"],
                    success=True,
                ),
                final_solution="print('merged')",
                final_score=0.87,
            )
        
        # Mock Phase 2 graph
        async def mock_phase2_run(task, initial_solution, initial_score):
            return RefinementState(
                task=task,
                config=config,
                solution_state=SolutionState(
                    current_code="print('refined')",
                    validation_score=0.89,
                    ablation_summaries=["Feature engineering is important"],
                    refined_blocks=["def feature_eng(): pass"],
                ),
                outer_iteration=1,
                completed=True,
            )
        
        # Mock Phase 3 graph
        async def mock_phase3_run(task, solutions):
            return EnsembleState(
                task=task,
                config=config,
                solutions=solutions,
                attempts=[
                    EnsembleResult(
                        strategy="Weighted Average",
                        merged_code="print('ensemble')",
                        validation_score=0.91,
                        iteration=1,
                    ),
                ],
                best_result=EnsembleResult(
                    strategy="Weighted Average",
                    merged_code="print('ensemble')",
                    validation_score=0.91,
                    iteration=1,
                ),
                iteration=1,
                completed=True,
            )
        
        # Replace graph run methods
        orchestrator._initial_solution_graph.run = mock_phase1_run
        orchestrator._refinement_graph.run = mock_phase2_run
        orchestrator._ensemble_graph.run = mock_phase3_run
        
        # Run without submission generation (to avoid file system operations)
        state = asyncio.run(orchestrator.run(task, generate_submission=False))
        
        assert state.completed
        assert state.error is None
        assert state.final_solution == "print('ensemble')"
        assert state.final_score == pytest.approx(0.91)
        assert state.phase1_state is not None
        assert len(state.phase2_states) == 2  # parallel_runs = 2
        assert state.phase3_state is not None
    
    def test_pipeline_handles_phase1_failure(self):
        """Test that pipeline handles Phase 1 failure gracefully."""
        import asyncio
        
        config = MLEStarConfig()
        orchestrator = MLEStarOrchestrator(config=config)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock Phase 1 to fail
        async def mock_phase1_fail(task_input):
            return InitialSolutionState(
                task=task_input,
                config=config,
                error="Retriever failed: No models found",
            )
        
        orchestrator._initial_solution_graph.run = mock_phase1_fail
        
        state = asyncio.run(orchestrator.run(task, generate_submission=False))
        
        assert state.completed
        assert state.error is not None
        assert "Phase 1 failed" in state.error
    
    def test_pipeline_handles_all_phase2_failures(self):
        """Test that pipeline handles all Phase 2 runs failing."""
        import asyncio
        
        config = MLEStarConfig()
        orchestrator = MLEStarOrchestrator(config=config, parallel_runs=2)
        
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        
        # Mock Phase 1 to succeed
        async def mock_phase1_success(task_input):
            return InitialSolutionState(
                task=task_input,
                config=config,
                final_solution="print('initial')",
                final_score=0.8,
            )
        
        # Mock Phase 2 to fail
        async def mock_phase2_fail(task, initial_solution, initial_score):
            return RefinementState(
                task=task,
                config=config,
                solution_state=SolutionState(
                    current_code=initial_solution,
                    validation_score=initial_score,
                ),
                error="Refinement failed",
                completed=True,
            )
        
        orchestrator._initial_solution_graph.run = mock_phase1_success
        orchestrator._refinement_graph.run = mock_phase2_fail
        
        state = asyncio.run(orchestrator.run(task, generate_submission=False))
        
        assert state.completed
        assert state.error is not None
        assert "Phase 2" in state.error or "refinement" in state.error.lower()


class TestSubmissionGeneration:
    """Test submission file generation."""
    
    def test_submission_result_structure(self):
        """Test SubmissionResult dataclass structure."""
        result = SubmissionResult(
            success=True,
            submission_code="print('submission')",
            execution_result=None,
            submission_path="/output/submission.csv",
            original_code="print('original')",
        )
        
        assert result.success
        assert result.submission_code == "print('submission')"
        assert result.submission_path == "/output/submission.csv"
        assert result.original_code == "print('original')"
    
    def test_submission_result_failure(self):
        """Test SubmissionResult for failed submission."""
        result = SubmissionResult(
            success=False,
            submission_code="",
            execution_result=None,
            submission_path="",
            original_code="print('original')",
        )
        
        assert not result.success
        assert result.submission_code == ""


class TestOrchestratorStateTracking:
    """Test orchestrator state tracking during execution."""
    
    def test_state_tracks_current_phase(self):
        """Test that state tracks the current phase."""
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        config = MLEStarConfig()
        
        state = OrchestratorState(task=task, config=config)
        
        # Initial phase should be 0
        assert state.current_phase == 0
        
        # Update phase
        state.current_phase = 1
        assert state.current_phase == 1
        
        state.current_phase = 2
        assert state.current_phase == 2
        
        state.current_phase = 3
        assert state.current_phase == 3
    
    def test_state_tracks_completion(self):
        """Test that state tracks completion status."""
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        config = MLEStarConfig()
        
        state = OrchestratorState(task=task, config=config)
        
        assert not state.completed
        
        state.completed = True
        assert state.completed
    
    def test_state_tracks_errors(self):
        """Test that state tracks errors."""
        task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        config = MLEStarConfig()
        
        state = OrchestratorState(task=task, config=config)
        
        assert state.error is None
        
        state.error = "Something went wrong"
        assert state.error == "Something went wrong"
