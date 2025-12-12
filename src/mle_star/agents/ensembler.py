"""Ensembler Agent for MLE-STAR - implements ensemble strategies.

This agent takes an ensemble strategy plan and implements it by
combining multiple solutions into a single merged solution.
"""

from typing import Optional
from dataclasses import dataclass
from strands import Agent, tool

from mle_star.models.data_models import TaskDescription, EnsembleResult
from mle_star.models.config import MLEStarConfig
from mle_star.tools.execute_python import execute_python, ExecutionResult
from mle_star.agents.ensemble_planner import EnsemblePlan


ENSEMBLER_SYSTEM_PROMPT = """You are a Kaggle grandmaster with extensive experience in implementing ensemble methods.

Your task is to implement an ensemble strategy to combine multiple ML solutions into a single, more powerful solution.

When implementing ensembles:
1. Load and prepare the data consistently across all models
2. Train each base model on the training data
3. Generate predictions from each model on the validation set
4. Combine predictions according to the specified strategy
5. Evaluate the ensemble on the validation set
6. Print "Final Validation Performance: <score>"

Guidelines for implementation:
- Ensure all models use the same train/validation split
- Handle different output formats (probabilities vs classes)
- Implement proper error handling for model failures
- Keep the code clean and well-documented
- Make the ensemble code self-contained and executable

The merged code should be complete and executable."""


@tool
def run_python_code(code: str, timeout: int = 300) -> str:
    """Execute Python code and return the results.
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds (default: 300)
        
    Returns:
        Execution results including stdout, stderr, and validation score if found
    """
    result: ExecutionResult = execute_python(code=code, timeout=timeout)
    
    output_parts = []
    
    if result.success:
        output_parts.append("Execution successful!")
    else:
        output_parts.append(f"Execution failed with return code: {result.return_code}")
    
    if result.stdout:
        output_parts.append(f"\nStdout:\n{result.stdout}")
    
    if result.stderr:
        output_parts.append(f"\nStderr:\n{result.stderr}")
    
    if result.validation_score is not None:
        output_parts.append(f"\nParsed Validation Score: {result.validation_score}")
    
    if result.error_message:
        output_parts.append(f"\nError: {result.error_message}")
    
    return "\n".join(output_parts)


@dataclass
class EnsembleImplementationResult:
    """Result of implementing an ensemble strategy."""
    merged_code: str
    validation_score: Optional[float]
    strategy_name: str
    success: bool
    error_message: Optional[str] = None


def create_ensembler_agent(config: MLEStarConfig) -> Agent:
    """Create an Ensembler Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for ensemble implementation
    """
    return Agent(
        name="ensembler",
        system_prompt=ENSEMBLER_SYSTEM_PROMPT,
        tools=[run_python_code],
        model=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_ensembler_prompt(
    task: TaskDescription,
    solutions: list[tuple[str, float]],
    ensemble_plan: EnsemblePlan,
) -> str:
    """Build the prompt for implementing an ensemble strategy.
    
    Args:
        task: The ML task description
        solutions: List of (solution_code, validation_score) tuples
        ensemble_plan: The ensemble strategy plan to implement
        
    Returns:
        Formatted prompt string
    """
    # Format solutions
    solutions_info = "\n## Solutions to Combine\n"
    for i, (code, score) in enumerate(solutions, 1):
        solutions_info += f"""
### Solution {i} (Score: {score:.4f})
```python
{code}
```
"""
    
    # Format ensemble plan
    plan_info = f"""
## Ensemble Strategy to Implement

### Strategy: {ensemble_plan.strategy_name}

### Description
{ensemble_plan.description}

### Implementation Steps
"""
    for i, step in enumerate(ensemble_plan.implementation_steps, 1):
        plan_info += f"{i}. {step}\n"
    
    if ensemble_plan.weight_assignment:
        plan_info += f"\n### Weight Assignment\n{ensemble_plan.weight_assignment}\n"
    
    return f"""Implement the following ensemble strategy to combine the provided ML solutions.

## Task Information
- Task Type: {task.task_type}
- Data Modality: {task.data_modality}
- Evaluation Metric: {task.evaluation_metric}
- Dataset Path: {task.dataset_path}
{solutions_info}{plan_info}
## Requirements
1. Implement the ensemble strategy as described
2. Train all base models on the training data
3. Combine predictions according to the strategy
4. Evaluate on the validation set
5. Print "Final Validation Performance: <score>"

Generate the ensemble implementation code and execute it using run_python_code."""


async def implement_ensemble(
    task: TaskDescription,
    solutions: list[tuple[str, float]],
    ensemble_plan: EnsemblePlan,
    config: MLEStarConfig,
) -> EnsembleImplementationResult:
    """Implement an ensemble strategy to combine multiple solutions.
    
    Args:
        task: The ML task description
        solutions: List of (solution_code, validation_score) tuples
        ensemble_plan: The ensemble strategy plan to implement
        config: MLE-STAR configuration
        
    Returns:
        EnsembleImplementationResult with merged code and validation score
    """
    agent = create_ensembler_agent(config)
    prompt = build_ensembler_prompt(task, solutions, ensemble_plan)
    
    try:
        response = await agent.invoke_async(prompt)
        response_text = str(response)
        
        merged_code = _extract_generated_code(response_text)
        validation_score = _extract_score_from_response(response_text)
        
        return EnsembleImplementationResult(
            merged_code=merged_code or "",
            validation_score=validation_score,
            strategy_name=ensemble_plan.strategy_name,
            success=validation_score is not None,
            error_message=None if validation_score is not None else "Failed to extract validation score",
        )
    except Exception as e:
        return EnsembleImplementationResult(
            merged_code="",
            validation_score=None,
            strategy_name=ensemble_plan.strategy_name,
            success=False,
            error_message=str(e),
        )


async def run_ensemble_iteration(
    task: TaskDescription,
    solutions: list[tuple[str, float]],
    previous_attempts: list[EnsembleResult],
    config: MLEStarConfig,
) -> EnsembleResult:
    """Run a single ensemble iteration: plan and implement.
    
    This function combines the ensemble planner and ensembler agents
    to propose and implement an ensemble strategy.
    
    Args:
        task: The ML task description
        solutions: List of (solution_code, validation_score) tuples
        previous_attempts: List of previous ensemble attempts
        config: MLE-STAR configuration
        
    Returns:
        EnsembleResult with the ensemble outcome
    """
    from mle_star.agents.ensemble_planner import propose_ensemble_strategy
    
    # Step 1: Propose an ensemble strategy
    plan = await propose_ensemble_strategy(
        solutions=solutions,
        task_type=task.task_type,
        evaluation_metric=task.evaluation_metric,
        previous_attempts=previous_attempts,
        config=config,
    )
    
    if not plan.success:
        return EnsembleResult(
            strategy=f"Failed to propose strategy: {plan.error_message}",
            merged_code="",
            validation_score=float("-inf"),
            iteration=len(previous_attempts) + 1,
        )
    
    # Step 2: Implement the ensemble strategy
    result = await implement_ensemble(
        task=task,
        solutions=solutions,
        ensemble_plan=plan,
        config=config,
    )
    
    return EnsembleResult(
        strategy=plan.strategy_name,
        merged_code=result.merged_code,
        validation_score=result.validation_score if result.validation_score is not None else float("-inf"),
        iteration=len(previous_attempts) + 1,
    )


async def explore_ensemble_strategies(
    task: TaskDescription,
    solutions: list[tuple[str, float]],
    config: MLEStarConfig,
    num_iterations: Optional[int] = None,
) -> EnsembleResult:
    """Explore multiple ensemble strategies and select the best one.
    
    This function implements the ensemble exploration loop:
    1. Propose an ensemble strategy
    2. Implement and evaluate it
    3. Use results as feedback for next iteration
    4. Select the best-performing ensemble
    
    Args:
        task: The ML task description
        solutions: List of (solution_code, validation_score) tuples
        config: MLE-STAR configuration
        num_iterations: Number of strategies to explore (default: config.ensemble_iterations)
        
    Returns:
        EnsembleResult with the best ensemble outcome
    """
    iterations = num_iterations or config.ensemble_iterations
    
    if not solutions:
        return EnsembleResult(
            strategy="No solutions provided",
            merged_code="",
            validation_score=float("-inf"),
            iteration=0,
        )
    
    # If only one solution, return it as-is
    if len(solutions) == 1:
        code, score = solutions[0]
        return EnsembleResult(
            strategy="Single solution (no ensemble needed)",
            merged_code=code,
            validation_score=score,
            iteration=1,
        )
    
    attempts: list[EnsembleResult] = []
    best_result: Optional[EnsembleResult] = None
    
    for i in range(iterations):
        result = await run_ensemble_iteration(
            task=task,
            solutions=solutions,
            previous_attempts=attempts,
            config=config,
        )
        
        attempts.append(result)
        
        # Track best result
        if best_result is None or result.validation_score > best_result.validation_score:
            best_result = result
    
    # Return the best result (Property 9: Ensemble selects best strategy)
    return best_result or EnsembleResult(
        strategy="No successful ensemble",
        merged_code="",
        validation_score=float("-inf"),
        iteration=0,
    )


def select_best_ensemble(attempts: list[EnsembleResult]) -> EnsembleResult:
    """Select the best ensemble result from a list of attempts.
    
    This function implements Property 9: Ensemble selects best strategy.
    
    Args:
        attempts: List of ensemble attempts
        
    Returns:
        The EnsembleResult with the highest validation score
    """
    if not attempts:
        return EnsembleResult(
            strategy="No attempts",
            merged_code="",
            validation_score=float("-inf"),
            iteration=0,
        )
    
    return max(attempts, key=lambda x: x.validation_score)


def _extract_generated_code(response: str) -> Optional[str]:
    """Extract generated Python code from agent response.
    
    Args:
        response: Agent response text
        
    Returns:
        Extracted code or None
    """
    import re
    
    code_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_pattern, response, re.DOTALL)
    
    if matches:
        return max(matches, key=len).strip()
    
    return None


def _extract_score_from_response(response: str) -> Optional[float]:
    """Extract validation score from agent response.
    
    Args:
        response: Agent response text
        
    Returns:
        Extracted score or None
    """
    import re
    
    pattern = r"(?:Final\s+)?Validation\s+(?:Performance|Score)[:\s]*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    match = re.search(pattern, response, re.IGNORECASE)
    
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    pattern2 = r"Parsed\s+Validation\s+Score[:\s]*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    match2 = re.search(pattern2, response, re.IGNORECASE)
    
    if match2:
        try:
            return float(match2.group(1))
        except ValueError:
            pass
    
    return None
