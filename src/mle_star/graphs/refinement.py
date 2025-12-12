"""Refinement Graph for MLE-STAR Phase 2.

This module implements the graph for Phase 2: Iterative Refinement.
The graph orchestrates:
1. Ablation Study Agent - identifies component impacts
2. Summarization Agent - parses ablation output
3. Extractor Agent - identifies most impactful code blocks
4. RefinementLoopNode - inner loop for refining code blocks

The graph supports cyclic execution for outer loop iterations.

Requirements: 7.2, 7.4, 7.5, 8.1, 8.2, 8.3
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
import asyncio

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import (
    TaskDescription,
    SolutionState,
    RefinementAttempt,
)
from mle_star.agents.ablation_study import run_ablation_study, AblationResult
from mle_star.agents.summarizer import summarize_ablation_results, AblationSummary
from mle_star.agents.extractor import extract_code_block, ExtractedBlock
from mle_star.agents.coder import refine_code_block, substitute_code_block
from mle_star.agents.planner import (
    propose_refinement_plan,
    format_plan_as_text,
    RefinementPlan,
)
from mle_star.agents.debugger import debug_with_retries_sync
from mle_star.tools.execute_python import execute_python
from mle_star.tools.refinement_utils import select_best_attempt, InnerLoopResult


@dataclass
class RefinementState:
    """State maintained throughout the refinement phase.
    
    Attributes:
        task: The ML task description
        config: MLE-STAR configuration
        solution_state: Current solution state
        ablation_result: Result of latest ablation study
        ablation_summary: Summary of latest ablation study
        extracted_block: Currently extracted code block
        inner_loop_result: Result of inner loop refinement
        outer_iteration: Current outer loop iteration
        completed: Whether refinement is complete
        error: Any error that occurred
    """
    task: TaskDescription
    config: MLEStarConfig
    solution_state: SolutionState
    ablation_result: Optional[AblationResult] = None
    ablation_summary: Optional[AblationSummary] = None
    extracted_block: Optional[ExtractedBlock] = None
    inner_loop_result: Optional[InnerLoopResult] = None
    outer_iteration: int = 0
    completed: bool = False
    error: Optional[str] = None


class RefinementLoopNode:
    """Custom node implementing the inner refinement loop.
    
    This node executes the inner loop logic:
    1. Start with the initial refinement plan from the extractor
    2. For each iteration:
       - Implement the plan using the coder agent
       - Substitute the refined block into the solution
       - Execute and evaluate the solution
       - If not the last iteration, propose a new plan
    3. Select the best-performing attempt
    
    Requirements: 7.2, 7.4, 7.5
    """
    
    def __init__(self, config: MLEStarConfig):
        """Initialize the refinement loop node.
        
        Args:
            config: MLE-STAR configuration
        """
        self.config = config
    
    async def execute(
        self,
        state: RefinementState,
    ) -> RefinementState:
        """Execute the inner refinement loop.
        
        Args:
            state: Current refinement state
            
        Returns:
            Updated state with inner loop results
        """
        if state.error or not state.extracted_block:
            return state
        
        extracted = state.extracted_block
        current_solution = state.solution_state.current_code
        initial_score = state.solution_state.validation_score
        
        attempts: list[RefinementAttempt] = []
        best_score = initial_score
        best_solution = current_solution
        
        # Get initial plan from extractor
        current_plan = extracted.refinement_plan
        
        # Inner loop iterations
        for i in range(self.config.inner_loop_iterations):
            try:
                # Implement the plan using coder agent
                refined_result = await refine_code_block(
                    code_block=extracted.code_block,
                    refinement_plan=current_plan,
                    config=self.config,
                    context=f"Target metric: {state.task.evaluation_metric}",
                )
                
                if not refined_result.success:
                    # Skip this iteration if refinement failed
                    continue
                
                # Substitute refined block into solution
                candidate_solution = substitute_code_block(
                    full_solution=current_solution,
                    original_block=extracted.code_block,
                    refined_block=refined_result.refined_code,
                )
                
                # Execute and evaluate the candidate solution
                score = await self._evaluate_solution(candidate_solution)
                
                # Record the attempt
                attempt = RefinementAttempt(
                    plan=current_plan,
                    refined_code_block=refined_result.refined_code,
                    full_solution=candidate_solution,
                    validation_score=score,
                    iteration=i,
                )
                attempts.append(attempt)
                
                # Track best solution (Requirements 7.5)
                if score > best_score:
                    best_score = score
                    best_solution = candidate_solution
                
                # If not the last iteration, propose a new plan
                if i < self.config.inner_loop_iterations - 1:
                    new_plan = await propose_refinement_plan(
                        code_block=extracted.code_block,
                        previous_attempts=attempts,
                        config=self.config,
                        target_metric=state.task.evaluation_metric,
                    )
                    if new_plan.success:
                        current_plan = format_plan_as_text(new_plan)
                        
            except Exception as e:
                # Log error but continue with other iterations
                continue
        
        # Select best attempt (Requirements 7.4)
        inner_result = select_best_attempt(attempts, initial_score)
        
        # Update state with results
        state.inner_loop_result = inner_result
        
        # Update solution state if we improved
        if inner_result.improved and inner_result.best_attempt:
            state.solution_state.current_code = inner_result.best_attempt.full_solution
            state.solution_state.validation_score = inner_result.best_score
            state.solution_state.refined_blocks.append(extracted.code_block)
        
        return state
    
    async def _evaluate_solution(self, code: str) -> float:
        """Execute and evaluate a solution.
        
        Args:
            code: Python code to execute
            
        Returns:
            Validation score from execution
        """
        result = execute_python(code=code, timeout=300)
        
        if result.validation_score is not None:
            return result.validation_score
        
        # If execution failed, try debugging
        if not result.success and result.stderr:
            debug_result = debug_with_retries_sync(
                code=code,
                error=result.stderr,
                config=self.config,
            )
            if debug_result.success and debug_result.corrected_code:
                retry_result = execute_python(code=debug_result.corrected_code, timeout=300)
                if retry_result.validation_score is not None:
                    return retry_result.validation_score
        
        # Return negative infinity if we couldn't get a score
        return float("-inf")


class RefinementGraph:
    """Graph orchestrator for Phase 2: Iterative Refinement.
    
    This class implements a cyclic graph with the following nodes:
    - ablation: Runs ablation study to identify component impacts
    - summarize: Parses ablation output and extracts insights
    - extract: Identifies most impactful code block for refinement
    - refine: Inner loop for refining the extracted block
    
    The graph supports cyclic execution for outer loop iterations.
    
    Requirements: 8.1, 8.2, 8.3
    """
    
    # Maximum node executions for safety (prevents infinite loops)
    MAX_NODE_EXECUTIONS = 50
    
    def __init__(self, config: MLEStarConfig):
        """Initialize the graph with configuration.
        
        Args:
            config: MLE-STAR configuration
        """
        self.config = config
        self._nodes: dict[str, Callable] = {}
        self._edges: list[tuple[str, str, Optional[Callable]]] = []
        self._entry_point: str = ""
        self._refinement_loop = RefinementLoopNode(config)
        
        # Build the graph
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the graph structure with nodes and edges."""
        # Add nodes
        self._nodes["ablation"] = self._ablation_node
        self._nodes["summarize"] = self._summarize_node
        self._nodes["extract"] = self._extract_node
        self._nodes["refine"] = self._refine_node
        
        # Define edges (source, target, condition)
        # Sequential flow through the pipeline
        self._edges = [
            ("ablation", "summarize", None),
            ("summarize", "extract", None),
            ("extract", "refine", None),
            # Conditional edge back to ablation for outer loop
            ("refine", "ablation", self._should_continue_outer_loop),
        ]
        
        # Set entry point
        self._entry_point = "ablation"
    
    def _should_continue_outer_loop(self, state: RefinementState) -> bool:
        """Determine if the outer loop should continue.
        
        Args:
            state: Current refinement state
            
        Returns:
            True if outer loop should continue
        """
        # Check if we've reached max iterations (Requirements 8.1)
        if state.outer_iteration >= self.config.outer_loop_iterations:
            return False
        
        # Check for errors
        if state.error:
            return False
        
        # Check if marked as completed
        if state.completed:
            return False
        
        return True
    
    async def _ablation_node(self, state: RefinementState) -> RefinementState:
        """Execute the ablation study node.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with ablation results
        """
        if state.error:
            return state
        
        try:
            ablation_result = await run_ablation_study(
                state.task,
                state.solution_state,
                state.config,
            )
            state.ablation_result = ablation_result
            
            if not ablation_result.success:
                state.error = f"Ablation study failed: {ablation_result.error_message}"
                
        except Exception as e:
            state.error = f"Ablation node failed: {str(e)}"
        
        return state
    
    async def _summarize_node(self, state: RefinementState) -> RefinementState:
        """Execute the summarization node.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with ablation summary
        """
        if state.error or not state.ablation_result:
            return state
        
        try:
            summary = await summarize_ablation_results(
                state.ablation_result.raw_output,
                state.config,
            )
            state.ablation_summary = summary
            
            # Record the summary in solution state (Requirements 8.2)
            if summary.success:
                state.solution_state.ablation_summaries.append(summary.raw_summary)
            else:
                state.error = f"Summarization failed: {summary.error_message}"
                
        except Exception as e:
            state.error = f"Summarize node failed: {str(e)}"
        
        return state
    
    async def _extract_node(self, state: RefinementState) -> RefinementState:
        """Execute the extraction node.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with extracted code block
        """
        if state.error or not state.ablation_summary:
            return state
        
        try:
            extracted = await extract_code_block(
                state.solution_state,
                state.ablation_summary,
                state.config,
            )
            state.extracted_block = extracted
            
            if not extracted.success:
                state.error = f"Extraction failed: {extracted.error_message}"
                
        except Exception as e:
            state.error = f"Extract node failed: {str(e)}"
        
        return state
    
    async def _refine_node(self, state: RefinementState) -> RefinementState:
        """Execute the refinement inner loop node.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with refinement results
        """
        if state.error or not state.extracted_block:
            return state
        
        try:
            # Execute the inner loop
            state = await self._refinement_loop.execute(state)
            
            # Increment outer iteration counter (Requirements 8.2)
            state.outer_iteration += 1
            state.solution_state.outer_iteration = state.outer_iteration
            
        except Exception as e:
            state.error = f"Refine node failed: {str(e)}"
        
        return state
    
    def _get_next_node(
        self,
        current_node: str,
        state: RefinementState,
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
        initial_solution: str,
        initial_score: float,
    ) -> RefinementState:
        """Execute the refinement graph.
        
        Args:
            task: The ML task description
            initial_solution: Initial solution code from Phase 1
            initial_score: Initial validation score
            
        Returns:
            Final state after graph execution
        """
        # Initialize state
        solution_state = SolutionState(
            current_code=initial_solution,
            validation_score=initial_score,
            ablation_summaries=[],
            refined_blocks=[],
            outer_iteration=0,
            inner_iteration=0,
        )
        
        state = RefinementState(
            task=task,
            config=self.config,
            solution_state=solution_state,
        )
        
        # Track node executions for safety
        node_executions = 0
        
        # Execute nodes
        current_node = self._entry_point
        
        while current_node and node_executions < self.MAX_NODE_EXECUTIONS:
            node_func = self._nodes.get(current_node)
            if node_func:
                state = await node_func(state)
                node_executions += 1
                
                # Stop if error occurred
                if state.error:
                    break
            
            # Get next node (may loop back for outer iterations)
            next_node = self._get_next_node(current_node, state)
            
            # If we're at refine and should continue, loop back
            if current_node == "refine" and next_node == "ablation":
                if not self._should_continue_outer_loop(state):
                    break
            
            current_node = next_node
        
        # Mark as completed
        state.completed = True
        
        return state
    
    def run_sync(
        self,
        task: TaskDescription,
        initial_solution: str,
        initial_score: float,
    ) -> RefinementState:
        """Synchronous wrapper for running the graph.
        
        Args:
            task: The ML task description
            initial_solution: Initial solution code from Phase 1
            initial_score: Initial validation score
            
        Returns:
            Final state after graph execution
        """
        return asyncio.run(self.run(task, initial_solution, initial_score))


def create_refinement_graph(config: MLEStarConfig) -> RefinementGraph:
    """Factory function to create a RefinementGraph.
    
    Args:
        config: MLE-STAR configuration
        
    Returns:
        Configured RefinementGraph instance
    """
    return RefinementGraph(config)
