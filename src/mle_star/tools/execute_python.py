"""Python code execution tool for MLE-STAR agents."""

import subprocess
import sys
import tempfile
import re
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class ExecutionResult:
    """Result of Python code execution."""
    stdout: str
    stderr: str
    return_code: int
    validation_score: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None


def parse_validation_score(output: str) -> Optional[float]:
    """Parse 'Final Validation Performance:' from execution output.
    
    Args:
        output: The stdout from code execution
        
    Returns:
        The parsed validation score, or None if not found
    """
    pattern = r"Final Validation Performance:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)"
    match = re.search(pattern, output)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def execute_python(
    code: str,
    timeout: int = 300,
    working_dir: Optional[str] = None
) -> ExecutionResult:
    """Execute Python code in a subprocess with timeout.
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds (default: 300)
        working_dir: Working directory for execution (default: temp dir)
        
    Returns:
        ExecutionResult containing stdout, stderr, return code, and parsed score
    """
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(code)
        script_path = f.name
    
    try:
        # Determine working directory
        cwd = working_dir if working_dir else Path(script_path).parent
        
        # Execute the script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        
        stdout = result.stdout
        stderr = result.stderr
        return_code = result.returncode
        
        # Parse validation score from output
        validation_score = parse_validation_score(stdout)
        
        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            return_code=return_code,
            validation_score=validation_score,
            success=(return_code == 0),
            error_message=stderr if return_code != 0 else None
        )
        
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="",
            stderr=f"Execution timed out after {timeout} seconds",
            return_code=-1,
            validation_score=None,
            success=False,
            error_message=f"Execution timed out after {timeout} seconds"
        )
    except Exception as e:
        return ExecutionResult(
            stdout="",
            stderr=str(e),
            return_code=-1,
            validation_score=None,
            success=False,
            error_message=str(e)
        )
    finally:
        # Clean up temporary file
        try:
            Path(script_path).unlink()
        except OSError:
            pass
