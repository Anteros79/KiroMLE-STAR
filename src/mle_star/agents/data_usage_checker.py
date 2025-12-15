"""Data Usage Checker Agent for MLE-STAR - verifies all data files are used.

This agent analyzes solutions to ensure all provided data files are utilized
and revises solutions to incorporate missing files.
"""

from dataclasses import dataclass
from typing import Optional
from strands import Agent

from mle_star.models.config import MLEStarConfig
from mle_star.models.model_factory import create_model
from mle_star.models.data_models import TaskDescription


DATA_USAGE_CHECKER_SYSTEM_PROMPT = """You are a data science expert specializing in ensuring comprehensive data utilization in machine learning solutions.

Your task is to verify that all provided data files are being used in the solution and to revise the solution to incorporate any missing data sources.

When analyzing data usage:
1. Identify all data files mentioned in the task description
2. Check which files are actually loaded and used in the solution code
3. Determine if any data sources are being ignored

When incorporating missing data:
1. Understand the purpose of each unused data file
2. Determine how it could enhance the solution (additional features, auxiliary targets, etc.)
3. Add appropriate code to load and integrate the missing data
4. Ensure proper merging/joining with existing data

Common ways to incorporate additional data:
- Merge on common keys (IDs, timestamps)
- Use as additional features
- Use for data augmentation
- Use for validation/cross-referencing

Return the complete revised code that incorporates all data sources."""


@dataclass
class DataUsageCheckResult:
    """Result of data usage checking.
    
    Attributes:
        all_files_used: Whether all data files are used
        provided_files: List of files mentioned in task description
        used_files: List of files actually used in the code
        missing_files: List of files not used in the code
        revised_code: The revised code incorporating all files
        original_code: The original code that was analyzed
    """
    all_files_used: bool
    provided_files: list[str]
    used_files: list[str]
    missing_files: list[str]
    revised_code: str
    original_code: str


def create_data_usage_checker_agent(config: MLEStarConfig) -> Agent:
    """Create a Data Usage Checker Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for data usage checking
    """
    return Agent(
        name="data_usage_checker",
        system_prompt=DATA_USAGE_CHECKER_SYSTEM_PROMPT,
        tools=[],
        model=create_model(config),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def extract_data_files_from_task(task: TaskDescription) -> list[str]:
    """Extract data file references from task description.
    
    Args:
        task: The task description
        
    Returns:
        List of data file paths/names mentioned in the task
    """
    import re
    
    files = []
    text = task.description
    
    # Common data file patterns
    patterns = [
        r'["\']([^"\']+\.csv)["\']',
        r'["\']([^"\']+\.parquet)["\']',
        r'["\']([^"\']+\.json)["\']',
        r'["\']([^"\']+\.xlsx?)["\']',
        r'["\']([^"\']+\.tsv)["\']',
        r'["\']([^"\']+\.feather)["\']',
        r'["\']([^"\']+\.pkl)["\']',
        r'["\']([^"\']+\.pickle)["\']',
        r'\b(train\.csv|test\.csv|sample_submission\.csv)\b',
        r'\b(train_data|test_data|validation_data)\.csv\b',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        files.extend(matches)
    
    # Also check dataset_path
    if task.dataset_path:
        if ',' in task.dataset_path:
            files.extend([f.strip() for f in task.dataset_path.split(',')])
        else:
            files.append(task.dataset_path)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in files:
        if f.lower() not in seen:
            seen.add(f.lower())
            unique_files.append(f)
    
    return unique_files


def extract_used_files_from_code(code: str) -> list[str]:
    """Extract data files that are actually used in the code.
    
    Args:
        code: The solution code
        
    Returns:
        List of data file paths/names used in the code
    """
    import re
    
    files = []
    
    # Patterns for file loading
    patterns = [
        r'pd\.read_csv\(["\']([^"\']+)["\']',
        r'pd\.read_parquet\(["\']([^"\']+)["\']',
        r'pd\.read_json\(["\']([^"\']+)["\']',
        r'pd\.read_excel\(["\']([^"\']+)["\']',
        r'pd\.read_feather\(["\']([^"\']+)["\']',
        r'pd\.read_pickle\(["\']([^"\']+)["\']',
        r'open\(["\']([^"\']+\.(?:csv|json|txt|parquet))["\']',
        r'np\.load\(["\']([^"\']+)["\']',
        r'np\.loadtxt\(["\']([^"\']+)["\']',
        r'load_data\(["\']([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, code, re.IGNORECASE)
        files.extend(matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in files:
        # Extract just the filename for comparison
        filename = f.split('/')[-1].split('\\')[-1]
        if filename.lower() not in seen:
            seen.add(filename.lower())
            unique_files.append(f)
    
    return unique_files


def find_missing_files(provided: list[str], used: list[str]) -> list[str]:
    """Find files that are provided but not used.
    
    Args:
        provided: List of provided data files
        used: List of used data files
        
    Returns:
        List of files that are provided but not used
    """
    # Normalize filenames for comparison
    def normalize(f: str) -> str:
        return f.split('/')[-1].split('\\')[-1].lower()
    
    used_normalized = {normalize(f) for f in used}
    
    missing = []
    for f in provided:
        if normalize(f) not in used_normalized:
            missing.append(f)
    
    return missing


def build_data_usage_check_prompt(
    code: str,
    task: TaskDescription,
    provided_files: list[str],
    missing_files: list[str],
) -> str:
    """Build a prompt for the data usage checker agent.
    
    Args:
        code: The solution code to analyze
        task: The task description
        provided_files: List of all provided data files
        missing_files: List of files not currently used
        
    Returns:
        Formatted prompt string for the data usage checker agent
    """
    return f"""Analyze the following solution and incorporate the missing data files.

Task Description:
{task.description}

Provided Data Files:
{', '.join(provided_files)}

Currently Missing/Unused Files:
{', '.join(missing_files)}

Current Solution Code:
```python
{code}
```

Please revise the solution to incorporate the missing data files ({', '.join(missing_files)}).
Consider how each file could enhance the solution (additional features, auxiliary data, etc.).

Return the complete revised code that uses ALL provided data files.

Format your response as:
ANALYSIS:
[Brief explanation of how each missing file will be incorporated]

REVISED_CODE:
```python
[Complete revised code here]
```"""


def parse_data_usage_response(
    response: str,
    original_code: str,
    provided_files: list[str],
    used_files: list[str],
    missing_files: list[str],
) -> DataUsageCheckResult:
    """Parse the data usage checker agent's response.
    
    Args:
        response: The agent's response
        original_code: The original code
        provided_files: List of provided files
        used_files: List of used files
        missing_files: List of missing files
        
    Returns:
        DataUsageCheckResult with parsed information
    """
    import re
    
    # Extract revised code
    code_pattern = r'```(?:python)?\s*\n(.*?)```'
    code_matches = re.findall(code_pattern, response, re.DOTALL)
    
    if code_matches:
        revised_code = code_matches[-1].strip()
    else:
        revised_code = original_code
    
    # Check if all files are now used in the revised code
    new_used_files = extract_used_files_from_code(revised_code)
    new_missing = find_missing_files(provided_files, new_used_files)
    
    return DataUsageCheckResult(
        all_files_used=len(new_missing) == 0,
        provided_files=provided_files,
        used_files=new_used_files,
        missing_files=new_missing,
        revised_code=revised_code,
        original_code=original_code,
    )


async def check_data_usage(
    code: str,
    task: TaskDescription,
    config: MLEStarConfig,
    agent: Optional[Agent] = None,
) -> DataUsageCheckResult:
    """Check if all data files are used and revise if needed.
    
    Args:
        code: The solution code to analyze
        task: The task description with data file information
        config: MLE-STAR configuration
        agent: Optional pre-created agent
        
    Returns:
        DataUsageCheckResult with analysis and revised code
    """
    if agent is None:
        agent = create_data_usage_checker_agent(config)
    
    # Extract files
    provided_files = extract_data_files_from_task(task)
    used_files = extract_used_files_from_code(code)
    missing_files = find_missing_files(provided_files, used_files)
    
    # If all files are used, return early
    if not missing_files:
        return DataUsageCheckResult(
            all_files_used=True,
            provided_files=provided_files,
            used_files=used_files,
            missing_files=[],
            revised_code=code,
            original_code=code,
        )
    
    # Build prompt and get revised code
    prompt = build_data_usage_check_prompt(code, task, provided_files, missing_files)
    response = await agent.invoke_async(prompt)
    
    return parse_data_usage_response(
        str(response),
        code,
        provided_files,
        used_files,
        missing_files,
    )


def check_data_usage_sync(
    code: str,
    task: TaskDescription,
    config: MLEStarConfig,
    agent: Optional[Agent] = None,
) -> DataUsageCheckResult:
    """Synchronous version of check_data_usage.
    
    Args:
        code: The solution code to analyze
        task: The task description
        config: MLE-STAR configuration
        agent: Optional pre-created agent
        
    Returns:
        DataUsageCheckResult with analysis and revised code
    """
    import asyncio
    return asyncio.run(check_data_usage(code, task, config, agent))
