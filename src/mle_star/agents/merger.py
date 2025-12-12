"""Merger Agent for MLE-STAR - combines model solutions into ensembles.

This agent merges multiple model candidates into a single solution by
creating ensembles. It processes candidates in descending score order
and stops when performance degrades.
"""

from typing import Optional
from dataclasses import dataclass
from strands import Agent, tool

from mle_star.models.data_models import TaskDescription, ModelCandidate
from mle_star.models.config import MLEStarConfig
from mle_star.tools.execute_python import execute_python, ExecutionResult


MERGER_SYSTEM_PROMPT = """You are a Kaggle grandmaster with extensive experience in creating ensemble models.

Your task is to integrate multiple model solutions into a single, more powerful ensemble solution.

When merging models:
1. Train each model separately on the training data
2. Create a simple average ensemble of predictions
3. Keep similar functionality together for maintainability
4. Ensure the merged solution is self-contained and executable

Guidelines for merging:
- Start with the best-performing model as the base
- Add models one at a time to the ensemble
- Use simple averaging for regression tasks
- Use voting or probability averaging for classification
- Maintain proper train/validation splits
- Print "Final Validation Performance: <score>" after evaluation

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
class MergeResult:
    """Result of a merge operation."""
    merged_code: str
    validation_score: Optional[float]
    models_included: list[str]
    success: bool
    error_message: Optional[str] = None


def create_merger_agent(config: MLEStarConfig) -> Agent:
    """Create a Merger Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for model merging
    """
    return Agent(
        name="merger",
        system_prompt=MERGER_SYSTEM_PROMPT,
        tools=[run_python_code],
        model=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_merge_prompt(
    task: TaskDescription,
    base_solution: ModelCandidate,
    reference_solution: ModelCandidate,
    current_ensemble_code: Optional[str] = None,
) -> str:
    """Build the prompt for merging two model solutions.
    
    Args:
        task: The ML task description
        base_solution: The current best solution (or ensemble)
        reference_solution: The solution to merge in
        current_ensemble_code: Current ensemble code if already merged
        
    Returns:
        Formatted prompt string
    """
    base_code = current_ensemble_code or base_solution.generated_code or base_solution.example_code
    ref_code = reference_solution.generated_code or reference_solution.example_code
    
    return f"""Integrate the reference solution into the base solution to create an ensemble.

## Task Information
- Task Type: {task.task_type}
- Data Modality: {task.data_modality}
- Evaluation Metric: {task.evaluation_metric}
- Dataset Path: {task.dataset_path}

## Base Solution (Current Best)
Model: {base_solution.name}
Score: {base_solution.validation_score}
```python
{base_code or "# No code available"}
```

## Reference Solution (To Merge)
Model: {reference_solution.name}
Score: {reference_solution.validation_score}
```python
{ref_code or "# No code available"}
```

## Requirements
1. Create an ensemble that combines both models
2. Train both models on the training data
3. Average their predictions (or use voting for classification)
4. Evaluate the ensemble on the validation set
5. Print "Final Validation Performance: <score>"

Generate the merged ensemble code and execute it using run_python_code."""


async def merge_two_solutions(
    task: TaskDescription,
    base_solution: ModelCandidate,
    reference_solution: ModelCandidate,
    config: MLEStarConfig,
    current_ensemble_code: Optional[str] = None,
) -> MergeResult:
    """Merge two model solutions into an ensemble.
    
    Args:
        task: The ML task description
        base_solution: The current best solution
        reference_solution: The solution to merge in
        config: MLE-STAR configuration
        current_ensemble_code: Current ensemble code if already merged
        
    Returns:
        MergeResult with merged code and validation score
    """
    agent = create_merger_agent(config)
    prompt = build_merge_prompt(task, base_solution, reference_solution, current_ensemble_code)
    
    try:
        response = await agent.invoke_async(prompt)
        response_text = str(response)
        
        merged_code = _extract_generated_code(response_text)
        validation_score = _extract_score_from_response(response_text)
        
        return MergeResult(
            merged_code=merged_code or "",
            validation_score=validation_score,
            models_included=[base_solution.name, reference_solution.name],
            success=validation_score is not None,
            error_message=None if validation_score is not None else "Failed to extract validation score",
        )
    except Exception as e:
        return MergeResult(
            merged_code="",
            validation_score=None,
            models_included=[base_solution.name, reference_solution.name],
            success=False,
            error_message=str(e),
        )


async def merge_candidates_sequentially(
    task: TaskDescription,
    candidates: list[ModelCandidate],
    config: MLEStarConfig,
) -> MergeResult:
    """Merge model candidates sequentially, stopping when performance degrades.
    
    This implements the MLE-STAR merging strategy:
    1. Sort candidates by validation score (descending)
    2. Start with the best candidate as base
    3. Sequentially try to merge each subsequent candidate
    4. Stop when a merge results in worse performance
    
    Args:
        task: The ML task description
        candidates: List of evaluated model candidates (will be sorted)
        config: MLE-STAR configuration
        
    Returns:
        MergeResult with the final merged solution
    """
    # Filter candidates with valid scores and sort descending
    valid_candidates = [c for c in candidates if c.validation_score is not None]
    
    if not valid_candidates:
        return MergeResult(
            merged_code="",
            validation_score=None,
            models_included=[],
            success=False,
            error_message="No candidates with valid scores to merge",
        )
    
    valid_candidates.sort(key=lambda c: c.validation_score, reverse=True)  # type: ignore
    
    if len(valid_candidates) == 1:
        # Only one candidate, return it as-is
        best = valid_candidates[0]
        return MergeResult(
            merged_code=best.generated_code or best.example_code or "",
            validation_score=best.validation_score,
            models_included=[best.name],
            success=True,
        )
    
    # Start with the best candidate
    current_best = valid_candidates[0]
    current_score = current_best.validation_score
    current_code = current_best.generated_code or current_best.example_code or ""
    models_included = [current_best.name]
    
    # Try to merge each subsequent candidate
    for candidate in valid_candidates[1:]:
        merge_result = await merge_two_solutions(
            task=task,
            base_solution=current_best,
            reference_solution=candidate,
            config=config,
            current_ensemble_code=current_code if len(models_included) > 1 else None,
        )
        
        if not merge_result.success or merge_result.validation_score is None:
            # Merge failed, continue with current best
            continue
        
        # Check if merge improved performance
        if merge_result.validation_score > current_score:  # type: ignore
            # Merge improved performance, update current best
            current_score = merge_result.validation_score
            current_code = merge_result.merged_code
            models_included.append(candidate.name)
            
            # Update current_best to represent the ensemble
            current_best = ModelCandidate(
                name=f"Ensemble({', '.join(models_included)})",
                description=f"Ensemble of {len(models_included)} models",
                example_code="",
                validation_score=current_score,
                generated_code=current_code,
            )
        else:
            # Performance degraded, stop merging (per Requirements 4.4)
            break
    
    return MergeResult(
        merged_code=current_code,
        validation_score=current_score,
        models_included=models_included,
        success=True,
    )


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
