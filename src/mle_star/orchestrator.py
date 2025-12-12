"""Main orchestrator for MLE-STAR multi-agent pipeline.

This module implements the MLEStarOrchestrator class that coordinates
all three phases of the MLE-STAR pipeline:
- Phase 1: Initial Solution Generation
- Phase 2: Iterative Refinement
- Phase 3: Ensemble

Requirements: 1.1, 9.1, 10.3
"""

from dataclasses import dataclass, field
from typing import Optional
import asyncio
import logging

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import (
    TaskDescription,
    SolutionState,
    EnsembleResult,
)
from mle_star.graphs.initial_solution import (
    InitialSolutionGraph,
    InitialSolutionState,
)
from mle_star.graphs.refinement import (
    RefinementGraph,
    RefinementState,
)
from mle_star.graphs.ensemble import (
    EnsembleGraph,
    EnsembleState,
)
from mle_star.agents.submission import generate_submission, SubmissionResult


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class OrchestratorState:
    """State maintained throughout the orchestrator execution.
    
    Attributes:
        task: The ML task description
        config: MLE-STAR configuration
        phase1_state: State from Phase 1 (Initial Solution)
        phase2_states: States from Phase 2 (Refinement) - one per parallel run
        phase3_state: State from Phase 3 (Ensemble)
        submission_result: Result of submission generation
        final_solution: The final solution code
        final_score: The final validation score
        current_phase: Current phase being executed (1, 2, or 3)
        error: Any error that occurred
        completed: Whether orchestration is complete
    """
    task: TaskDescription
    config: MLEStarConfig
    phase1_state: Optional[InitialSolutionState] = None
    phase2_states: list[RefinementState] = field(default_factory=list)
    phase3_state: Optional[EnsembleState] = None
    submission_result: Optional[SubmissionResult] = None
    final_solution: str = ""
    final_score: Optional[float] = None
    current_phase: int = 0
    error: Optional[str] = None
    completed: bool = False


class MLEStarOrchestrator:
    """Main orchestrator for the MLE-STAR multi-agent pipeline.
    
    This class coordinates all three phases of the MLE-STAR pipeline:
    
    Phase 1 - Initial Solution Generation:
        - Retrieves model candidates from web search
        - Evaluates each candidate
        - Merges best candidates into initial solution
        - Runs data leakage and usage checks
    
    Phase 2 - Iterative Refinement:
        - Runs ablation studies to identify impactful components
        - Extracts and refines code blocks
        - Supports parallel runs for ensemble diversity
    
    Phase 3 - Ensemble:
        - Combines multiple refined solutions
        - Explores different ensemble strategies
        - Selects best performing ensemble
    
    Requirements: 1.1
    """
    
    # Number of parallel refinement runs for ensemble diversity
    DEFAULT_PARALLEL_RUNS = 3
    
    def __init__(
        self,
        config: Optional[MLEStarConfig] = None,
        parallel_runs: int = DEFAULT_PARALLEL_RUNS,
    ):
        """Initialize the orchestrator with configuration.
        
        Args:
            config: MLE-STAR configuration. If None, uses defaults.
            parallel_runs: Number of parallel refinement runs for ensemble.
        """
        self.config = config or MLEStarConfig()
        self.parallel_runs = parallel_runs
        
        # Initialize graphs
        self._initial_solution_graph = InitialSolutionGraph(self.config)
        self._refinement_graph = RefinementGraph(self.config)
        self._ensemble_graph = EnsembleGraph(self.config)
        
        # State management
        self._state: Optional[OrchestratorState] = None
        
        logger.info(
            f"MLEStarOrchestrator initialized with config: "
            f"num_retrieved_models={self.config.num_retrieved_models}, "
            f"inner_loop_iterations={self.config.inner_loop_iterations}, "
            f"outer_loop_iterations={self.config.outer_loop_iterations}, "
            f"ensemble_iterations={self.config.ensemble_iterations}, "
            f"parallel_runs={self.parallel_runs}"
        )
    
    @property
    def state(self) -> Optional[OrchestratorState]:
        """Get the current orchestrator state."""
        return self._state
    
    def _create_checkpoint(self, phase: int) -> dict:
        """Create a checkpoint of the current state for recovery.
        
        Args:
            phase: The phase number being checkpointed
            
        Returns:
            Dictionary containing checkpoint data
        """
        if not self._state:
            return {}
        
        checkpoint = {
            "phase": phase,
            "task_description": self._state.task.description,
            "config": self.config.to_dict(),
        }
        
        if self._state.phase1_state:
            checkpoint["phase1_solution"] = self._state.phase1_state.final_solution
            checkpoint["phase1_score"] = self._state.phase1_state.final_score
        
        if self._state.phase2_states:
            checkpoint["phase2_solutions"] = [
                {
                    "code": s.solution_state.current_code,
                    "score": s.solution_state.validation_score,
                }
                for s in self._state.phase2_states
            ]
        
        if self._state.phase3_state and self._state.phase3_state.best_result:
            checkpoint["phase3_solution"] = self._state.phase3_state.best_result.merged_code
            checkpoint["phase3_score"] = self._state.phase3_state.best_result.validation_score
        
        return checkpoint
    
    def _recover_from_checkpoint(
        self,
        checkpoint: dict,
        task: TaskDescription,
    ) -> int:
        """Recover state from a checkpoint.
        
        Args:
            checkpoint: Checkpoint data
            task: The task description
            
        Returns:
            The phase to resume from
        """
        self._state = OrchestratorState(task=task, config=self.config)
        
        phase = checkpoint.get("phase", 0)
        
        # Recover Phase 1 state if available
        if "phase1_solution" in checkpoint:
            self._state.phase1_state = InitialSolutionState(
                task=task,
                config=self.config,
                final_solution=checkpoint["phase1_solution"],
                final_score=checkpoint.get("phase1_score"),
            )
        
        # Recover Phase 2 states if available
        if "phase2_solutions" in checkpoint:
            for sol_data in checkpoint["phase2_solutions"]:
                solution_state = SolutionState(
                    current_code=sol_data["code"],
                    validation_score=sol_data["score"],
                )
                ref_state = RefinementState(
                    task=task,
                    config=self.config,
                    solution_state=solution_state,
                    completed=True,
                )
                self._state.phase2_states.append(ref_state)
        
        return phase

    async def _run_phase1(self, task: TaskDescription) -> InitialSolutionState:
        """Execute Phase 1: Initial Solution Generation.
        
        Args:
            task: The ML task description
            
        Returns:
            State from Phase 1 execution
        """
        logger.info("Starting Phase 1: Initial Solution Generation")
        self._state.current_phase = 1
        
        try:
            state = await self._initial_solution_graph.run(task)
            
            if state.error:
                logger.error(f"Phase 1 failed: {state.error}")
            else:
                logger.info(
                    f"Phase 1 completed. Score: {state.final_score}, "
                    f"Solution length: {len(state.final_solution)} chars"
                )
            
            return state
            
        except Exception as e:
            logger.exception(f"Phase 1 exception: {e}")
            error_state = InitialSolutionState(
                task=task,
                config=self.config,
                error=str(e),
            )
            return error_state
    
    async def _run_phase2_single(
        self,
        task: TaskDescription,
        initial_solution: str,
        initial_score: float,
        run_id: int,
    ) -> RefinementState:
        """Execute a single Phase 2 refinement run.
        
        Args:
            task: The ML task description
            initial_solution: Initial solution from Phase 1
            initial_score: Initial validation score
            run_id: Identifier for this parallel run
            
        Returns:
            State from Phase 2 execution
        """
        logger.info(f"Starting Phase 2 refinement run {run_id}")
        
        try:
            state = await self._refinement_graph.run(
                task=task,
                initial_solution=initial_solution,
                initial_score=initial_score,
            )
            
            if state.error:
                logger.error(f"Phase 2 run {run_id} failed: {state.error}")
            else:
                logger.info(
                    f"Phase 2 run {run_id} completed. "
                    f"Final score: {state.solution_state.validation_score}, "
                    f"Iterations: {state.outer_iteration}"
                )
            
            return state
            
        except Exception as e:
            logger.exception(f"Phase 2 run {run_id} exception: {e}")
            solution_state = SolutionState(
                current_code=initial_solution,
                validation_score=initial_score,
            )
            error_state = RefinementState(
                task=task,
                config=self.config,
                solution_state=solution_state,
                error=str(e),
                completed=True,
            )
            return error_state
    
    async def _run_phase2_parallel(
        self,
        task: TaskDescription,
        initial_solution: str,
        initial_score: float,
    ) -> list[RefinementState]:
        """Execute Phase 2 with parallel refinement runs.
        
        Runs multiple refinement pipelines in parallel to generate
        diverse solutions for the ensemble phase.
        
        Args:
            task: The ML task description
            initial_solution: Initial solution from Phase 1
            initial_score: Initial validation score
            
        Returns:
            List of states from parallel Phase 2 executions
        
        Requirements: 9.1
        """
        logger.info(f"Starting Phase 2: Iterative Refinement ({self.parallel_runs} parallel runs)")
        self._state.current_phase = 2
        
        # Create tasks for parallel execution
        tasks = [
            self._run_phase2_single(task, initial_solution, initial_score, i)
            for i in range(self.parallel_runs)
        ]
        
        # Execute all refinement runs in parallel
        states = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, handling any exceptions
        valid_states = []
        for i, state in enumerate(states):
            if isinstance(state, Exception):
                logger.error(f"Phase 2 run {i} raised exception: {state}")
                # Create error state for failed run
                solution_state = SolutionState(
                    current_code=initial_solution,
                    validation_score=initial_score,
                )
                error_state = RefinementState(
                    task=task,
                    config=self.config,
                    solution_state=solution_state,
                    error=str(state),
                    completed=True,
                )
                valid_states.append(error_state)
            else:
                valid_states.append(state)
        
        logger.info(f"Phase 2 completed. {len(valid_states)} solutions generated.")
        return valid_states

    async def _run_phase3(
        self,
        task: TaskDescription,
        solutions: list[tuple[str, float]],
    ) -> EnsembleState:
        """Execute Phase 3: Ensemble.
        
        Args:
            task: The ML task description
            solutions: List of (solution_code, validation_score) tuples
            
        Returns:
            State from Phase 3 execution
        """
        logger.info(f"Starting Phase 3: Ensemble ({len(solutions)} solutions)")
        self._state.current_phase = 3
        
        try:
            state = await self._ensemble_graph.run(task=task, solutions=solutions)
            
            if state.error:
                logger.error(f"Phase 3 failed: {state.error}")
            elif state.best_result:
                logger.info(
                    f"Phase 3 completed. Best strategy: {state.best_result.strategy}, "
                    f"Score: {state.best_result.validation_score}"
                )
            
            return state
            
        except Exception as e:
            logger.exception(f"Phase 3 exception: {e}")
            error_state = EnsembleState(
                task=task,
                config=self.config,
                solutions=solutions,
                error=str(e),
                completed=True,
            )
            return error_state
    
    async def _generate_submission(
        self,
        task: TaskDescription,
        solution: str,
    ) -> SubmissionResult:
        """Generate the final submission file.
        
        Args:
            task: The ML task description
            solution: The final solution code
            
        Returns:
            SubmissionResult with submission code and execution result
        """
        logger.info("Generating final submission")
        
        try:
            result = await generate_submission(
                code=solution,
                task=task,
                config=self.config,
                execute=True,
                timeout=600,
            )
            
            if result.success:
                logger.info(f"Submission generated: {result.submission_path}")
            else:
                logger.error("Submission generation failed")
            
            return result
            
        except Exception as e:
            logger.exception(f"Submission generation exception: {e}")
            return SubmissionResult(
                success=False,
                submission_code="",
                execution_result=None,
                submission_path="",
                original_code=solution,
            )
    
    async def run(
        self,
        task: TaskDescription,
        generate_submission: bool = True,
        checkpoint: Optional[dict] = None,
    ) -> OrchestratorState:
        """Execute the full MLE-STAR pipeline.
        
        Runs all three phases in sequence:
        1. Initial Solution Generation
        2. Iterative Refinement (parallel runs)
        3. Ensemble
        
        Optionally generates a submission file at the end.
        
        Args:
            task: The ML task description
            generate_submission: Whether to generate submission file
            checkpoint: Optional checkpoint to resume from
            
        Returns:
            Final orchestrator state
            
        Requirements: 1.1, 10.3
        """
        logger.info(f"Starting MLE-STAR pipeline for task: {task.task_type}")
        
        # Initialize or recover state
        start_phase = 1
        if checkpoint:
            start_phase = self._recover_from_checkpoint(checkpoint, task)
            logger.info(f"Resuming from checkpoint at phase {start_phase}")
        else:
            self._state = OrchestratorState(task=task, config=self.config)
        
        try:
            # Phase 1: Initial Solution Generation
            if start_phase <= 1:
                self._state.phase1_state = await self._run_phase1(task)
                
                if self._state.phase1_state.error:
                    self._state.error = f"Phase 1 failed: {self._state.phase1_state.error}"
                    self._state.completed = True
                    return self._state
                
                # Create checkpoint after Phase 1
                self._create_checkpoint(1)
            
            # Get initial solution for Phase 2
            initial_solution = self._state.phase1_state.final_solution
            initial_score = self._state.phase1_state.final_score or 0.0
            
            # Phase 2: Iterative Refinement (parallel runs)
            if start_phase <= 2:
                self._state.phase2_states = await self._run_phase2_parallel(
                    task=task,
                    initial_solution=initial_solution,
                    initial_score=initial_score,
                )
                
                # Check if all Phase 2 runs failed
                all_failed = all(s.error for s in self._state.phase2_states)
                if all_failed:
                    self._state.error = "All Phase 2 refinement runs failed"
                    self._state.completed = True
                    return self._state
                
                # Create checkpoint after Phase 2
                self._create_checkpoint(2)
            
            # Collect solutions for ensemble
            solutions: list[tuple[str, float]] = []
            for ref_state in self._state.phase2_states:
                if not ref_state.error:
                    solutions.append((
                        ref_state.solution_state.current_code,
                        ref_state.solution_state.validation_score,
                    ))
            
            # If no valid solutions, use initial solution
            if not solutions:
                solutions = [(initial_solution, initial_score)]
            
            # Phase 3: Ensemble
            if start_phase <= 3:
                self._state.phase3_state = await self._run_phase3(
                    task=task,
                    solutions=solutions,
                )
                
                # Create checkpoint after Phase 3
                self._create_checkpoint(3)
            
            # Set final solution
            if self._state.phase3_state and self._state.phase3_state.best_result:
                self._state.final_solution = self._state.phase3_state.best_result.merged_code
                self._state.final_score = self._state.phase3_state.best_result.validation_score
            elif solutions:
                # Fallback to best individual solution
                best_solution = max(solutions, key=lambda x: x[1])
                self._state.final_solution = best_solution[0]
                self._state.final_score = best_solution[1]
            
            # Generate submission if requested
            if generate_submission and self._state.final_solution:
                self._state.submission_result = await self._generate_submission(
                    task=task,
                    solution=self._state.final_solution,
                )
            
            self._state.completed = True
            logger.info(
                f"MLE-STAR pipeline completed. Final score: {self._state.final_score}"
            )
            
        except Exception as e:
            logger.exception(f"Pipeline exception: {e}")
            self._state.error = str(e)
            self._state.completed = True
        
        return self._state
    
    def run_sync(
        self,
        task: TaskDescription,
        generate_submission: bool = True,
        checkpoint: Optional[dict] = None,
    ) -> OrchestratorState:
        """Synchronous wrapper for running the pipeline.
        
        Args:
            task: The ML task description
            generate_submission: Whether to generate submission file
            checkpoint: Optional checkpoint to resume from
            
        Returns:
            Final orchestrator state
        """
        return asyncio.run(self.run(task, generate_submission, checkpoint))



def create_orchestrator(
    config: Optional[MLEStarConfig] = None,
    parallel_runs: int = MLEStarOrchestrator.DEFAULT_PARALLEL_RUNS,
) -> MLEStarOrchestrator:
    """Factory function to create an MLEStarOrchestrator.
    
    Args:
        config: MLE-STAR configuration. If None, uses defaults.
        parallel_runs: Number of parallel refinement runs for ensemble.
        
    Returns:
        Configured MLEStarOrchestrator instance
    """
    return MLEStarOrchestrator(config=config, parallel_runs=parallel_runs)
