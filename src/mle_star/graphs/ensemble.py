"""Ensemble Graph for MLE-STAR Phase 3.

This module implements the graph for Phase 3: Ensemble.
The graph orchestrates:
1. Ensemble Planner Agent - proposes ensemble strategies
2. Ensembler Agent - implements ensemble strategies

The graph supports iterative exploration of ensemble strategies.

Requirements: 9.5
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
import asyncio

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import TaskDescription, EnsembleResult
from mle_star.agents.ensemble_planner import (
    propose_ensemble_strategy,
    EnsemblePlan,
)
from mle_star.agents.ensembler import (
    implement_ensemble,
    select_best_ensemble,
    EnsembleImplementationResult,
)


@dataclass
class EnsembleState:
    """State maintained throughout the ensemble phase.
    
    Attributes:
        task: The ML task description
        config: MLE-STAR configuration
        solutions: List of (solution_code, validation_score) tuples to ensemble
        current_plan: Current ensemble strategy plan
        current_result: Result of current ensemble implementation
        attempts: All ensemble attempts made
        best_result: Best ensemble result so far
        iteration: Current iteration number
        completed: Whether ensemble exploration is complete
        error: Any error that occurred
    """
    task: TaskDescription
    config: MLEStarConfig
    solutions: list[tuple[str, float]] = field(default_factory=list)
    current_plan: Optional[EnsemblePlan] = None
    current_result: Optional[EnsembleImplementationResult] = None
    attempts: list[EnsembleResult] = field(default_factory=list)
    best_result: Optional[EnsembleResult] = None
    iteration: int = 0
    completed: bool = False
    error: Optional[str] = None


class EnsembleGraph:
    """Graph orchestrator for Phase 3: Ensemble.
    
    This class implements a graph with the following nodes:
    - ensemble_planner: Proposes ensemble strategies
    - ensembler: Implements ensemble strategies
    
    The graph supports iterative exploration with conditional edges.
    
    Requirements: 9.5
    """
    
    def __init__(self, config: MLEStarConfig):
        """Initialize the graph with configuration.
        
        Args:
            config: MLE-STAR configuration
        """
        self.config = config
        self._nodes: dict[str, Callable] = {}
        self._edges: list[tuple[str, str, Optional[Callable]]] = []
        self._entry_point: str = ""
        
        # Build the graph
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the graph structure with nodes and edges."""
        # Add nodes
        self._nodes["ensemble_planner"] = self._ensemble_planner_node
        self._nodes["ensembler"] = self._ensembler_node
        
        # Define edges (source, target, condition)
        self._edges = [
            ("ensemble_planner", "ensembler", None),
            # Conditional edge back to planner for iteration
            ("ensembler", "ensemble_planner", self._should_continue_iteration),
        ]
        
        # Set entry point
        self._entry_point = "ensemble_planner"
    
    def _should_continue_iteration(self, state: EnsembleState) -> bool:
        """Determine if ensemble exploration should continue.
        
        Args:
            state: Current ensemble state
            
        Returns:
            True if exploration should continue
        """
        # Check if we've reached max iterations
        if state.iteration >= self.config.ensemble_iterations:
            return False
        
        # Check for errors
        if state.error:
            return False
        
        # Check if marked as completed
        if state.completed:
            return False
        
        return True
    
    async def _ensemble_planner_node(self, state: EnsembleState) -> EnsembleState:
        """Execute the ensemble planner node.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with ensemble plan
        """
        if state.error:
            return state
        
        if not state.solutions:
            state.error = "No solutions provided for ensemble"
            return state
        
        try:
            # Convert attempts to EnsembleResult format for feedback
            previous_attempts = state.attempts
            
            plan = await propose_ensemble_strategy(
                solutions=state.solutions,
                task_type=state.task.task_type,
                evaluation_metric=state.task.evaluation_metric,
                previous_attempts=previous_attempts,
                config=state.config,
            )
            
            state.current_plan = plan
            
            if not plan.success:
                state.error = f"Ensemble planning failed: {plan.error_message}"
                
        except Exception as e:
            state.error = f"Ensemble planner node failed: {str(e)}"
        
        return state
    
    async def _ensembler_node(self, state: EnsembleState) -> EnsembleState:
        """Execute the ensembler node.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with ensemble result
        """
        if state.error or not state.current_plan:
            return state
        
        try:
            result = await implement_ensemble(
                task=state.task,
                solutions=state.solutions,
                ensemble_plan=state.current_plan,
                config=state.config,
            )
            
            state.current_result = result
            
            # Create EnsembleResult and add to attempts
            ensemble_result = EnsembleResult(
                strategy=state.current_plan.strategy_name,
                merged_code=result.merged_code,
                validation_score=result.validation_score if result.validation_score is not None else float("-inf"),
                iteration=state.iteration + 1,
            )
            state.attempts.append(ensemble_result)
            
            # Update best result if this is better
            if state.best_result is None or (
                result.validation_score is not None and
                result.validation_score > state.best_result.validation_score
            ):
                state.best_result = ensemble_result
            
            # Increment iteration counter
            state.iteration += 1
            
        except Exception as e:
            state.error = f"Ensembler node failed: {str(e)}"
        
        return state
    
    def _get_next_node(
        self,
        current_node: str,
        state: EnsembleState,
    ) -> Optional[str]:
        """Get the next node in the graph after the current node.
        
        Args:
            current_node: Name of the current node
            state: Current state for evaluating conditions
            
        Returns:
            Name of the next node, or None if at end
        """
        for source, target, condition in self._edges:
            if source == current_node:
                # Check condition if present
                if condition is None or condition(state):
                    return target
        return None
    
    async def run(
        self,
        task: TaskDescription,
        solutions: list[tuple[str, float]],
    ) -> EnsembleState:
        """Execute the ensemble graph.
        
        Args:
            task: The ML task description
            solutions: List of (solution_code, validation_score) tuples
            
        Returns:
            Final state after graph execution
        """
        # Handle edge cases
        if not solutions:
            state = EnsembleState(
                task=task,
                config=self.config,
                error="No solutions provided for ensemble",
                completed=True,
            )
            return state
        
        # If only one solution, return it as-is
        if len(solutions) == 1:
            code, score = solutions[0]
            result = EnsembleResult(
                strategy="Single solution (no ensemble needed)",
                merged_code=code,
                validation_score=score,
                iteration=1,
            )
            state = EnsembleState(
                task=task,
                config=self.config,
                solutions=solutions,
                attempts=[result],
                best_result=result,
                iteration=1,
                completed=True,
            )
            return state
        
        # Initialize state
        state = EnsembleState(
            task=task,
            config=self.config,
            solutions=solutions,
        )
        
        # Execute nodes
        current_node = self._entry_point
        
        while current_node:
            node_func = self._nodes.get(current_node)
            if node_func:
                state = await node_func(state)
                
                # Stop if error occurred
                if state.error:
                    break
            
            # Get next node (may loop back for iterations)
            next_node = self._get_next_node(current_node, state)
            
            # If we're at ensembler and should continue, loop back
            if current_node == "ensembler" and next_node == "ensemble_planner":
                if not self._should_continue_iteration(state):
                    break
            
            current_node = next_node
        
        # Mark as completed
        state.completed = True
        
        # Ensure we have a best result
        if not state.best_result and state.attempts:
            state.best_result = select_best_ensemble(state.attempts)
        
        return state
    
    def run_sync(
        self,
        task: TaskDescription,
        solutions: list[tuple[str, float]],
    ) -> EnsembleState:
        """Synchronous wrapper for running the graph.
        
        Args:
            task: The ML task description
            solutions: List of (solution_code, validation_score) tuples
            
        Returns:
            Final state after graph execution
        """
        return asyncio.run(self.run(task, solutions))


def create_ensemble_graph(config: MLEStarConfig) -> EnsembleGraph:
    """Factory function to create an EnsembleGraph.
    
    Args:
        config: MLE-STAR configuration
        
    Returns:
        Configured EnsembleGraph instance
    """
    return EnsembleGraph(config)
