"""Debugger Agent for MLE-STAR - analyzes tracebacks and fixes code errors.

This agent analyzes error tracebacks from code execution and attempts to fix
the code, with configurable retry logic.
"""

from dataclasses import dataclass
from typing import Optional
from strands import Agent

from mle_star.models.config import MLEStarConfig
from mle_star.models.model_factory import create_model
from mle_star.tools.execute_python import execute_python, ExecutionResult


DEBUGGER_SYSTEM_PROMPT = """You are an expert Python debugger specializing in ML pipeline errors and their resolution.

<objective>
Analyze error tracebacks, identify root causes, and produce corrected code that executes successfully.
</objective>

<diagnosis_process>
1. READ: Parse the full traceback from bottom to top (most recent call last)
2. LOCATE: Identify the exact file, line number, and code causing the error
3. CLASSIFY: Determine the error category (see below)
4. DIAGNOSE: Understand WHY the error occurred in this context
5. FIX: Apply the minimal correction that resolves the issue
6. VERIFY: Mentally trace through the fix to ensure it works
</diagnosis_process>

<error_categories>
IMPORT_ERROR:
- Cause: Missing package or wrong module name
- Fix: Add correct import, suggest pip install if needed

TYPE_ERROR:
- Cause: Wrong data type passed to function
- Fix: Add type conversion (int(), float(), np.array(), .values)

SHAPE_ERROR (ValueError with shape):
- Cause: Array dimension mismatch
- Fix: Reshape, transpose, or adjust indexing

VALUE_ERROR:
- Cause: Invalid parameter value
- Fix: Correct the parameter to valid range/type

KEY_ERROR:
- Cause: Missing dictionary key or DataFrame column
- Fix: Check column names, add fallback with .get()

INDEX_ERROR:
- Cause: Array index out of bounds
- Fix: Add bounds checking, adjust indexing

ATTRIBUTE_ERROR:
- Cause: Object doesn't have the method/attribute
- Fix: Check object type, use correct API

MEMORY_ERROR:
- Cause: Out of memory
- Fix: Reduce batch size, use generators, downsample

FILE_NOT_FOUND:
- Cause: Wrong file path
- Fix: Correct path, add existence check
</error_categories>

<fix_principles>
1. MINIMAL: Make the smallest change that fixes the error
2. PRESERVE: Don't refactor or "improve" unrelated code
3. DEFENSIVE: Add checks to prevent recurrence
4. COMPATIBLE: Ensure fix works with rest of pipeline
5. DOCUMENTED: Add comment explaining the fix
</fix_principles>

<output_format>
Return the COMPLETE corrected code (not just the fix).
The code must be immediately executable.
Add a comment at the fix location:
```python
# FIX: [description of what was wrong and how it was fixed]
```
</output_format>

<learning_from_history>
If previous fix attempts failed:
1. Analyze WHY they failed (different root cause?)
2. Try a DIFFERENT approach (not just tweaking the same fix)
3. Consider if the error indicates a DEEPER issue
4. Look for patterns across multiple failures
</learning_from_history>

<thinking>
When debugging, ask:
- What is the actual vs expected behavior?
- What changed that might have caused this?
- Is this a symptom of a deeper problem?
- What's the simplest fix that addresses the root cause?
</thinking>"""


@dataclass
class DebugResult:
    """Result of a debugging attempt.
    
    Attributes:
        success: Whether the debugging was successful
        corrected_code: The corrected code (or last attempted code)
        execution_result: The execution result of the corrected code
        attempts_made: Number of debugging attempts made
        error_history: List of errors encountered during debugging
    """
    success: bool
    corrected_code: str
    execution_result: Optional[ExecutionResult]
    attempts_made: int
    error_history: list[str]


def create_debugger_agent(config: MLEStarConfig) -> Agent:
    """Create a Debugger Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for debugging
    """
    return Agent(
        name="debugger",
        system_prompt=DEBUGGER_SYSTEM_PROMPT,
        tools=[],
        model=create_model(config),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_debug_prompt(
    original_code: str,
    error_traceback: str,
    previous_attempts: Optional[list[tuple[str, str]]] = None
) -> str:
    """Build a prompt for the debugger agent.
    
    Args:
        original_code: The code that failed to execute
        error_traceback: The error traceback from execution
        previous_attempts: Optional list of (attempted_code, error) tuples from previous attempts
        
    Returns:
        Formatted prompt string for the debugger agent
    """
    prompt_parts = [
        "The following Python code failed to execute:\n",
        "```python",
        original_code,
        "```\n",
        "Error traceback:",
        "```",
        error_traceback,
        "```\n",
    ]
    
    if previous_attempts:
        prompt_parts.append("Previous debugging attempts that also failed:\n")
        for i, (code, error) in enumerate(previous_attempts, 1):
            prompt_parts.extend([
                f"Attempt {i}:",
                "```python",
                code[:500] + "..." if len(code) > 500 else code,
                "```",
                f"Error: {error[:300]}...\n" if len(error) > 300 else f"Error: {error}\n",
            ])
    
    prompt_parts.append(
        "Please analyze the error and provide the complete corrected code. "
        "Return only the corrected Python code without any explanation."
    )
    
    return "\n".join(prompt_parts)


def extract_code_from_debug_response(response: str) -> str:
    """Extract Python code from the debugger's response.
    
    Args:
        response: The debugger agent's response
        
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
    
    # If no code blocks, assume the entire response is code
    # Remove any leading/trailing explanation
    lines = response.strip().split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        # Skip obvious explanation lines
        if line.strip().startswith(('#', '//', '/*', '*')):
            if in_code:
                code_lines.append(line)
            continue
        if any(keyword in line.lower() for keyword in ['here is', 'the fix', 'corrected', 'solution:']):
            continue
        code_lines.append(line)
        in_code = True
    
    return '\n'.join(code_lines).strip()


async def debug_code(
    code: str,
    error_traceback: str,
    config: MLEStarConfig,
    agent: Optional[Agent] = None,
) -> tuple[str, bool]:
    """Attempt to debug code using the debugger agent.
    
    Args:
        code: The code that failed
        error_traceback: The error traceback
        config: MLE-STAR configuration
        agent: Optional pre-created agent (creates new one if not provided)
        
    Returns:
        Tuple of (corrected_code, success)
    """
    if agent is None:
        agent = create_debugger_agent(config)
    
    prompt = build_debug_prompt(code, error_traceback)
    response = await agent.invoke_async(prompt)
    corrected_code = extract_code_from_debug_response(str(response))
    
    return corrected_code, bool(corrected_code and corrected_code != code)


async def debug_with_retries(
    code: str,
    config: MLEStarConfig,
    last_working_code: Optional[str] = None,
    timeout: int = 300,
) -> DebugResult:
    """Debug code with retry logic up to max_debug_retries.
    
    This function executes the code, and if it fails, attempts to debug it
    up to max_debug_retries times. If all attempts fail, returns the last
    working version.
    
    Args:
        code: The code to execute and potentially debug
        config: MLE-STAR configuration with max_debug_retries
        last_working_code: Optional fallback code if all debugging fails
        timeout: Execution timeout in seconds
        
    Returns:
        DebugResult with the outcome of debugging attempts
    """
    agent = create_debugger_agent(config)
    current_code = code
    error_history: list[str] = []
    previous_attempts: list[tuple[str, str]] = []
    
    # First execution attempt
    result = execute_python(current_code, timeout=timeout)
    
    if result.success:
        return DebugResult(
            success=True,
            corrected_code=current_code,
            execution_result=result,
            attempts_made=0,
            error_history=[],
        )
    
    # Code failed, start debugging
    error_history.append(result.error_message or result.stderr)
    
    for attempt in range(config.max_debug_retries):
        error_traceback = result.error_message or result.stderr
        
        # Build prompt with history of previous attempts
        prompt = build_debug_prompt(current_code, error_traceback, previous_attempts)
        
        # Get corrected code from agent
        response = await agent.invoke_async(prompt)
        corrected_code = extract_code_from_debug_response(str(response))
        
        if not corrected_code or corrected_code == current_code:
            # Agent couldn't produce different code
            continue
        
        # Track this attempt
        previous_attempts.append((current_code, error_traceback))
        current_code = corrected_code
        
        # Try executing the corrected code
        result = execute_python(current_code, timeout=timeout)
        
        if result.success:
            return DebugResult(
                success=True,
                corrected_code=current_code,
                execution_result=result,
                attempts_made=attempt + 1,
                error_history=error_history,
            )
        
        error_history.append(result.error_message or result.stderr)
    
    # All attempts failed, return last working version or last attempted code
    final_code = last_working_code if last_working_code else current_code
    
    return DebugResult(
        success=False,
        corrected_code=final_code,
        execution_result=result,
        attempts_made=config.max_debug_retries,
        error_history=error_history,
    )


def debug_with_retries_sync(
    code: str,
    config: MLEStarConfig,
    last_working_code: Optional[str] = None,
    timeout: int = 300,
) -> DebugResult:
    """Synchronous version of debug_with_retries.
    
    Args:
        code: The code to execute and potentially debug
        config: MLE-STAR configuration with max_debug_retries
        last_working_code: Optional fallback code if all debugging fails
        timeout: Execution timeout in seconds
        
    Returns:
        DebugResult with the outcome of debugging attempts
    """
    import asyncio
    return asyncio.run(debug_with_retries(code, config, last_working_code, timeout))
