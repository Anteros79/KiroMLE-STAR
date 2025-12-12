"""Initial Solution Graph for MLE-STAR Phase 1.

This module implements the graph for Phase 1: Initial Solution Generation.
The graph orchestrates:
1. Retriever Agent - searches for effective ML models
2. Candidate Evaluator - evaluates each model candidate
3. Merger Agent - combines best candidates into ensemble
4. Data Leakage Checker - detects and corrects data leakage
5. Data Usage Checker - ensures all data files are used

Requirements: 14.4
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Callable
import asyncio

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import (
    TaskDescription,
    ModelCandidate,
    SolutionState,
)
from mle_star.agents.retriever import retrieve_models
from mle_star.agents.candidate_evaluator import (
    evaluate_all_candidates,
    sort_candidates_by_score,
)
from mle_star.agents.merger import merge_candidates_sequentially, MergeResult
from mle_star.agents.leakage_checker import check_for_leakage_sync, LeakageCheckResult
from mle_star.agents.data_usage_checker import check_data_usage_sync, DataUsageCheckResult


@dataclass
class InitialSolutionState:
    """State maintained throughout the initial solution generation phase.
    
    Attributes:
        task: The ML task description
        config: MLE-STAR configuration
        candidates: Retrieved model candidates
        evaluated_candidates: Candidates with validation scores
        merge_result: Result of merging candidates
        leakage_result: Result of data leakage check
        usage_result: Result of data usage check
        final_solution: The final solution code after all checks
        final_score: The final validation score
        error: Any error that occurred during execution
    """
    task: TaskDescription
    config: MLEStarConfig
    candidates: list[ModelCandidate] = field(default_factory=list)
    evaluated_candidates: list[ModelCandidate] = field(default_factory=list)
    merge_result: Optional[MergeResult] = None
    leakage_result: Optional[LeakageCheckResult] = None
    usage_result: Optional[DataUsageCheckResult] = None
    final_solution: str = ""
    final_score: Optional[float] = None
    error: Optional[str] = None


class InitialSolutionGraph:
    """Graph orchestrator for Phase 1: Initial Solution Generation.
    
    This class implements a sequential graph with the following nodes:
    - retriever: Searches web for effective ML models
    - evaluator: Evaluates each model candidate
    - merger: Combines best candidates into ensemble
    - leakage_check: Detects and corrects data leakage
    - usage_check: Ensures all data files are used
    
    The graph executes nodes sequentially, passing state between them.
    """
    
    def __init__(self, config: MLEStarConfig):
        """Initialize the graph with configuration.
        
        Args:
            config: MLE-STAR configuration
        """
        self.config = config
        self._nodes: dict[str, Callable] = {}
        self._edges: list[tuple[str, str]] = []
        self._entry_point: str = ""
        
        # Build the graph
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the graph structure with nodes and edges."""
        # Add nodes
        self._nodes["retriever"] = self._retriever_node
        self._nodes["evaluator"] = self._evaluator_node
        self._nodes["merger"] = self._merger_node
        self._nodes["leakage_check"] = self._leakage_check_node
        self._nodes["usage_check"] = self._usage_check_node
        
        # Define sequential edges
        self._edges = [
            ("retriever", "evaluator"),
            ("evaluator", "merger"),
            ("merger", "leakage_check"),
            ("leakage_check", "usage_check"),
        ]
        
        # Set entry point
        self._entry_point = "retriever"
    
    async def _retriever_node(self, state: InitialSolutionState) -> InitialSolutionState:
        """Execute the retriever node to search for ML models.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with retrieved candidates
        """
        try:
            candidates = await retrieve_models(state.task, state.config)
            state.candidates = candidates
        except Exception as e:
            state.error = f"Retriever failed: {str(e)}"
        return state
    
    async def _evaluator_node(self, state: InitialSolutionState) -> InitialSolutionState:
        """Execute the evaluator node to evaluate model candidates.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with evaluated candidates
        """
        if state.error:
            return state
        
        if not state.candidates:
            state.error = "No candidates to evaluate"
            return state
        
        try:
            evaluated = await evaluate_all_candidates(
                state.task,
                state.candidates,
                state.config,
            )
            state.evaluated_candidates = sort_candidates_by_score(evaluated)
        except Exception as e:
            state.error = f"Evaluator failed: {str(e)}"
        return state
    
    async def _merger_node(self, state: InitialSolutionState) -> InitialSolutionState:
        """Execute the merger node to combine model candidates.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with merged solution
        """
        if state.error:
            return state
        
        if not state.evaluated_candidates:
            state.error = "No evaluated candidates to merge"
            return state
        
        try:
            merge_result = await merge_candidates_sequentially(
                state.task,
                state.evaluated_candidates,
                state.config,
            )
            state.merge_result = merge_result
            state.final_solution = merge_result.merged_code
            state.final_score = merge_result.validation_score
        except Exception as e:
            state.error = f"Merger failed: {str(e)}"
        return state

    async def _leakage_check_node(self, state: InitialSolutionState) -> InitialSolutionState:
        """Execute the leakage check node to detect data leakage.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with leakage check result
        """
        if state.error:
            return state
        
        if not state.final_solution:
            state.error = "No solution to check for leakage"
            return state
        
        try:
            leakage_result = check_for_leakage_sync(
                state.final_solution,
                state.config,
            )
            state.leakage_result = leakage_result
            
            # If leakage was detected and corrected, update the solution
            if leakage_result.leakage_detected and leakage_result.corrected_code:
                state.final_solution = leakage_result.corrected_code
        except Exception as e:
            state.error = f"Leakage check failed: {str(e)}"
        return state
    
    async def _usage_check_node(self, state: InitialSolutionState) -> InitialSolutionState:
        """Execute the usage check node to verify all data files are used.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with usage check result
        """
        if state.error:
            return state
        
        if not state.final_solution:
            state.error = "No solution to check for data usage"
            return state
        
        try:
            usage_result = check_data_usage_sync(
                state.final_solution,
                state.task,
                state.config,
            )
            state.usage_result = usage_result
            
            # If missing files were found and corrected, update the solution
            if usage_result.missing_files and usage_result.revised_code:
                state.final_solution = usage_result.revised_code
        except Exception as e:
            state.error = f"Data usage check failed: {str(e)}"
        return state
    
    def _get_next_node(self, current_node: str) -> Optional[str]:
        """Get the next node in the graph after the current node.
        
        Args:
            current_node: Name of the current node
            
        Returns:
            Name of the next node, or None if at end
        """
        for source, target in self._edges:
            if source == current_node:
                return target
        return None
    
    async def run(self, task: TaskDescription) -> InitialSolutionState:
        """Execute the initial solution generation graph.
        
        Args:
            task: The ML task description
            
        Returns:
            Final state after graph execution
        """
        # Initialize state
        state = InitialSolutionState(task=task, config=self.config)
        
        # Execute nodes sequentially
        current_node = self._entry_point
        
        while current_node:
            node_func = self._nodes.get(current_node)
            if node_func:
                state = await node_func(state)
                
                # Stop if error occurred
                if state.error:
                    break
            
            current_node = self._get_next_node(current_node)
        
        return state
    
    def run_sync(self, task: TaskDescription) -> InitialSolutionState:
        """Synchronous wrapper for running the graph.
        
        Args:
            task: The ML task description
            
        Returns:
            Final state after graph execution
        """
        return asyncio.run(self.run(task))


def create_initial_solution_graph(config: MLEStarConfig) -> InitialSolutionGraph:
    """Factory function to create an InitialSolutionGraph.
    
    Args:
        config: MLE-STAR configuration
        
    Returns:
        Configured InitialSolutionGraph instance
    """
    return InitialSolutionGraph(config)
