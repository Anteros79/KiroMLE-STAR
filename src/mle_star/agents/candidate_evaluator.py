"""Candidate Evaluation Agent for MLE-STAR - evaluates model candidates.

This agent generates and executes Python code to evaluate each model candidate
on the given task, extracting validation scores from execution output.
"""

from typing import Optional
from strands import Agent, tool

from mle_star.models.data_models import TaskDescription, ModelCandidate
from mle_star.models.config import MLEStarConfig
from mle_star.models.model_factory import create_model
from mle_star.tools.execute_python import execute_python, ExecutionResult


CANDIDATE_EVAL_SYSTEM_PROMPT = """You are a rigorous ML engineer specializing in fair model evaluation and benchmarking.

<objective>
Generate and execute Python code that fairly evaluates a model candidate, producing reliable validation scores.
</objective>

<evaluation_protocol>
1. Data Loading: Load dataset, verify shape and types
2. Preprocessing: Apply task-appropriate transformations
3. Splitting: Use stratified 80/20 split with random_state=42
4. Training: Fit model with reasonable defaults
5. Evaluation: Compute metric on held-out validation set
6. Reporting: Print score in exact format below
</evaluation_protocol>

<code_requirements>
- Set random seeds: np.random.seed(42), random.seed(42)
- Handle missing values before model fitting
- Use try/except for graceful error handling
- Print warnings to stderr, results to stdout
- MUST print: "Final Validation Performance: {score:.6f}"
</code_requirements>

<metric_interpretation>
- For accuracy/AUC/F1: higher is better (0-1 scale)
- For RMSE/MAE/log_loss: lower is better
- Always report the raw metric value, not transformed
</metric_interpretation>

<error_handling>
If evaluation fails:
1. Print the error traceback to stderr
2. Attempt a simpler baseline model (e.g., LogisticRegression, Ridge)
3. Report "Final Validation Performance: -1.0" if all attempts fail
</error_handling>

<thinking>
Before generating code, consider:
- What preprocessing does this data modality require?
- Are there class imbalance issues to address?
- What's the appropriate cross-validation strategy?
</thinking>"""


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


def create_candidate_evaluator_agent(config: MLEStarConfig) -> Agent:
    """Create a Candidate Evaluation Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for candidate evaluation
    """
    return Agent(
        name="candidate_evaluator",
        system_prompt=CANDIDATE_EVAL_SYSTEM_PROMPT,
        tools=[run_python_code],
        model=create_model(config),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_evaluation_prompt(
    task: TaskDescription,
    candidate: ModelCandidate,
) -> str:
    """Build the prompt for evaluating a model candidate.
    
    Args:
        task: The ML task description
        candidate: The model candidate to evaluate
        
    Returns:
        Formatted prompt string
    """
    return f"""Generate Python code to evaluate the following model on the given task.

## Task Information
- Task Type: {task.task_type}
- Data Modality: {task.data_modality}
- Evaluation Metric: {task.evaluation_metric}
- Dataset Path: {task.dataset_path}
- Task Description: {task.description}

## Model to Evaluate
- Model Name: {candidate.name}
- Model Description: {candidate.description}

## Example Code (if available)
```python
{candidate.example_code if candidate.example_code else "# No example code provided"}
```

## Requirements
1. Generate complete, executable Python code
2. Load data from the dataset path
3. Implement the model approach described above
4. Split into train/validation sets
5. Train and evaluate the model
6. Print the result as: "Final Validation Performance: <score>"

Generate the evaluation code now and execute it using the run_python_code tool."""


async def evaluate_candidate(
    task: TaskDescription,
    candidate: ModelCandidate,
    config: MLEStarConfig,
) -> ModelCandidate:
    """Evaluate a single model candidate on the given task.
    
    This function creates an agent, generates evaluation code, executes it,
    and updates the candidate with the validation score.
    
    Args:
        task: The ML task description
        candidate: The model candidate to evaluate
        config: MLE-STAR configuration
        
    Returns:
        Updated ModelCandidate with validation_score and generated_code set
    """
    agent = create_candidate_evaluator_agent(config)
    prompt = build_evaluation_prompt(task, candidate)
    
    # Invoke the agent to generate and run evaluation code
    response = await agent.invoke_async(prompt)
    response_text = str(response)
    
    # Extract the generated code and score from the response
    generated_code = _extract_generated_code(response_text)
    validation_score = _extract_score_from_response(response_text)
    
    # Return updated candidate
    return ModelCandidate(
        name=candidate.name,
        description=candidate.description,
        example_code=candidate.example_code,
        validation_score=validation_score,
        generated_code=generated_code,
    )


async def evaluate_all_candidates(
    task: TaskDescription,
    candidates: list[ModelCandidate],
    config: MLEStarConfig,
) -> list[ModelCandidate]:
    """Evaluate all model candidates on the given task.
    
    Args:
        task: The ML task description
        candidates: List of model candidates to evaluate
        config: MLE-STAR configuration
        
    Returns:
        List of evaluated ModelCandidate objects with scores
    """
    evaluated = []
    
    for candidate in candidates:
        try:
            evaluated_candidate = await evaluate_candidate(task, candidate, config)
            evaluated.append(evaluated_candidate)
        except Exception as e:
            # If evaluation fails, keep the candidate but with no score
            evaluated.append(ModelCandidate(
                name=candidate.name,
                description=candidate.description,
                example_code=candidate.example_code,
                validation_score=None,
                generated_code=None,
            ))
    
    return evaluated


def _extract_generated_code(response: str) -> Optional[str]:
    """Extract generated Python code from agent response.
    
    Args:
        response: Agent response text
        
    Returns:
        Extracted code or None
    """
    import re
    
    # Look for code blocks
    code_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_pattern, response, re.DOTALL)
    
    if matches:
        # Return the longest code block
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
    
    # Look for the standard format
    pattern = r"(?:Final\s+)?Validation\s+(?:Performance|Score)[:\s]*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    match = re.search(pattern, response, re.IGNORECASE)
    
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    # Look for "Parsed Validation Score" from tool output
    pattern2 = r"Parsed\s+Validation\s+Score[:\s]*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    match2 = re.search(pattern2, response, re.IGNORECASE)
    
    if match2:
        try:
            return float(match2.group(1))
        except ValueError:
            pass
    
    return None


def sort_candidates_by_score(
    candidates: list[ModelCandidate],
    descending: bool = True,
) -> list[ModelCandidate]:
    """Sort model candidates by validation score.
    
    Candidates without scores are placed at the end.
    
    Args:
        candidates: List of evaluated candidates
        descending: If True, sort highest score first (default: True)
        
    Returns:
        Sorted list of candidates
    """
    # Separate candidates with and without scores
    with_scores = [c for c in candidates if c.validation_score is not None]
    without_scores = [c for c in candidates if c.validation_score is None]
    
    # Sort those with scores
    with_scores.sort(
        key=lambda c: c.validation_score,  # type: ignore
        reverse=descending,
    )
    
    return with_scores + without_scores
