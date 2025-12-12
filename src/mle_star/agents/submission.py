"""Test Submission Agent for MLE-STAR - generates submission code.

This agent generates submission code that loads test data, removes subsampling,
uses the full training set, and produces a submission.csv file.
"""

from dataclasses import dataclass
from typing import Optional
from strands import Agent

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import TaskDescription
from mle_star.tools.execute_python import execute_python, ExecutionResult


SUBMISSION_SYSTEM_PROMPT = """You are a Kaggle grandmaster expert at generating submission files for machine learning competitions.

Your task is to modify a solution to generate a proper submission file for test data.

When generating submission code:
1. Load the test data from the provided path
2. Remove any subsampling that was used during development/validation
3. Use the FULL training set for final model training
4. Apply the same preprocessing to test data as training data
5. Generate predictions for all test samples
6. Save predictions in the required submission format (usually submission.csv)

Important considerations:
- Ensure no data leakage from test to train
- Use the same feature engineering pipeline
- Handle any missing values in test data
- Match the exact submission format required
- Include proper column names and index handling

The submission file should be ready for direct upload to the competition platform.

Return the complete submission generation code."""


@dataclass
class SubmissionResult:
    """Result of submission generation.
    
    Attributes:
        success: Whether submission was generated successfully
        submission_code: The code that generates the submission
        execution_result: Result of executing the submission code
        submission_path: Path to the generated submission file
        original_code: The original solution code
    """
    success: bool
    submission_code: str
    execution_result: Optional[ExecutionResult]
    submission_path: str
    original_code: str


def create_submission_agent(config: MLEStarConfig) -> Agent:
    """Create a Test Submission Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for submission generation
    """
    return Agent(
        name="submission_generator",
        system_prompt=SUBMISSION_SYSTEM_PROMPT,
        tools=[],
        model=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def detect_subsampling(code: str) -> list[str]:
    """Detect subsampling patterns in code.
    
    Args:
        code: The solution code to analyze
        
    Returns:
        List of detected subsampling patterns
    """
    import re
    
    patterns = []
    
    # Common subsampling patterns
    subsampling_patterns = [
        (r'\.sample\(\s*(?:n\s*=\s*)?\d+', 'DataFrame.sample() call'),
        (r'\.head\(\s*\d+\s*\)', 'DataFrame.head() limiting rows'),
        (r'\[:(\d+)\]', 'Array slicing limiting rows'),
        (r'\.iloc\[\s*:\s*(\d+)', 'iloc slicing limiting rows'),
        (r'frac\s*=\s*0\.\d+', 'Fractional sampling'),
        (r'nrows\s*=\s*\d+', 'nrows parameter limiting rows'),
        (r'SAMPLE_SIZE\s*=\s*\d+', 'SAMPLE_SIZE constant'),
        (r'SUBSAMPLE\s*=\s*True', 'SUBSAMPLE flag'),
        (r'debug\s*=\s*True', 'Debug mode enabled'),
    ]
    
    for pattern, description in subsampling_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            patterns.append(description)
    
    return patterns


def build_submission_prompt(
    code: str,
    task: TaskDescription,
    subsampling_patterns: list[str],
) -> str:
    """Build a prompt for the submission agent.
    
    Args:
        code: The solution code
        task: The task description
        subsampling_patterns: Detected subsampling patterns to remove
        
    Returns:
        Formatted prompt string for the submission agent
    """
    submission_format = task.submission_format or "submission.csv with id and prediction columns"
    
    prompt_parts = [
        "Generate submission code for the following solution.\n",
        f"Task Description:\n{task.description}\n",
        f"Dataset Path: {task.dataset_path}",
        f"Submission Format: {submission_format}\n",
    ]
    
    if subsampling_patterns:
        prompt_parts.append(
            f"Detected subsampling patterns to REMOVE:\n"
            f"- {chr(10).join('- ' + p for p in subsampling_patterns)}\n"
        )
    
    prompt_parts.extend([
        "Current Solution Code:",
        "```python",
        code,
        "```\n",
        "Please generate the complete submission code that:",
        "1. Removes ALL subsampling (use full training data)",
        "2. Trains on the FULL training set",
        "3. Loads and processes test data",
        "4. Generates predictions for ALL test samples",
        f"5. Saves to '{submission_format}' in the correct format\n",
        "Return ONLY the complete Python code for generating the submission.",
    ])
    
    return "\n".join(prompt_parts)


def extract_submission_code(response: str) -> str:
    """Extract submission code from the agent's response.
    
    Args:
        response: The agent's response
        
    Returns:
        Extracted Python code
    """
    import re
    
    # Try to extract code from markdown code blocks
    code_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_pattern, response, re.DOTALL)
    
    if matches:
        # Return the longest code block
        return max(matches, key=len).strip()
    
    # If no code blocks, return the response as-is (might be raw code)
    return response.strip()


def remove_subsampling_from_code(code: str) -> str:
    """Remove common subsampling patterns from code.
    
    This is a heuristic-based removal that handles common patterns.
    The LLM agent should handle more complex cases.
    
    Args:
        code: The code to clean
        
    Returns:
        Code with subsampling patterns removed or modified
    """
    import re
    
    modified = code
    
    # Remove .sample() calls (replace with full data)
    modified = re.sub(r'\.sample\(\s*(?:n\s*=\s*)?\d+[^)]*\)', '', modified)
    
    # Remove .head() calls that limit data
    modified = re.sub(r'\.head\(\s*\d+\s*\)', '', modified)
    
    # Change SUBSAMPLE = True to False
    modified = re.sub(r'SUBSAMPLE\s*=\s*True', 'SUBSAMPLE = False', modified, flags=re.IGNORECASE)
    
    # Change debug = True to False
    modified = re.sub(r'debug\s*=\s*True', 'debug = False', modified, flags=re.IGNORECASE)
    
    # Remove nrows parameter from read_csv
    modified = re.sub(r',\s*nrows\s*=\s*\d+', '', modified)
    
    return modified


def verify_no_subsampling(code: str) -> bool:
    """Verify that code doesn't contain subsampling.
    
    Args:
        code: The code to verify
        
    Returns:
        True if no subsampling detected, False otherwise
    """
    patterns = detect_subsampling(code)
    return len(patterns) == 0


async def generate_submission(
    code: str,
    task: TaskDescription,
    config: MLEStarConfig,
    agent: Optional[Agent] = None,
    execute: bool = True,
    timeout: int = 600,
) -> SubmissionResult:
    """Generate submission code and optionally execute it.
    
    Args:
        code: The solution code
        task: The task description
        config: MLE-STAR configuration
        agent: Optional pre-created agent
        execute: Whether to execute the submission code
        timeout: Execution timeout in seconds
        
    Returns:
        SubmissionResult with the submission code and execution result
    """
    if agent is None:
        agent = create_submission_agent(config)
    
    # Detect subsampling patterns
    subsampling_patterns = detect_subsampling(code)
    
    # Build prompt and get submission code
    prompt = build_submission_prompt(code, task, subsampling_patterns)
    response = await agent.invoke_async(prompt)
    submission_code = extract_submission_code(str(response))
    
    # Verify no subsampling in generated code
    if not verify_no_subsampling(submission_code):
        # Try to remove remaining subsampling
        submission_code = remove_subsampling_from_code(submission_code)
    
    execution_result = None
    success = True
    submission_path = "submission.csv"
    
    if execute:
        execution_result = execute_python(submission_code, timeout=timeout)
        success = execution_result.success
        
        # Try to extract submission path from code
        import re
        path_match = re.search(r'\.to_csv\(["\']([^"\']+)["\']', submission_code)
        if path_match:
            submission_path = path_match.group(1)
    
    return SubmissionResult(
        success=success,
        submission_code=submission_code,
        execution_result=execution_result,
        submission_path=submission_path,
        original_code=code,
    )


def generate_submission_sync(
    code: str,
    task: TaskDescription,
    config: MLEStarConfig,
    agent: Optional[Agent] = None,
    execute: bool = True,
    timeout: int = 600,
) -> SubmissionResult:
    """Synchronous version of generate_submission.
    
    Args:
        code: The solution code
        task: The task description
        config: MLE-STAR configuration
        agent: Optional pre-created agent
        execute: Whether to execute the submission code
        timeout: Execution timeout in seconds
        
    Returns:
        SubmissionResult with the submission code and execution result
    """
    import asyncio
    return asyncio.run(generate_submission(code, task, config, agent, execute, timeout))
