"""Data Leakage Checker Agent for MLE-STAR - detects and corrects data leakage.

This agent analyzes preprocessing code for data leakage risks and generates
corrected code that uses only training statistics.
"""

from dataclasses import dataclass
from typing import Optional
from strands import Agent

from mle_star.models.config import MLEStarConfig


LEAKAGE_CHECKER_SYSTEM_PROMPT = """You are a data science expert specializing in detecting and preventing data leakage in machine learning pipelines.

Data leakage occurs when information from outside the training dataset is used to create the model, leading to overly optimistic performance estimates that don't generalize.

Common types of data leakage to detect:
1. **Target Leakage**: Using features that include information about the target variable
2. **Train-Test Contamination**: Using test/validation data statistics during training preprocessing
3. **Temporal Leakage**: Using future information to predict past events
4. **Feature Leakage**: Features that wouldn't be available at prediction time

When analyzing code, look for:
- Fitting scalers/encoders on the entire dataset before splitting
- Computing statistics (mean, std, min, max) on combined train+test data
- Using test data for feature selection or hyperparameter tuning
- Imputing missing values using statistics from the full dataset
- Target encoding without proper cross-validation

When correcting leakage:
1. Ensure all preprocessing is fit ONLY on training data
2. Transform test/validation data using training statistics
3. Use pipelines to prevent accidental leakage
4. Add comments explaining the correction

Return the complete corrected code with leakage issues fixed."""


@dataclass
class LeakageCheckResult:
    """Result of data leakage checking.
    
    Attributes:
        has_leakage: Whether data leakage was detected
        leakage_issues: List of detected leakage issues
        corrected_code: The corrected code (same as original if no leakage)
        original_code: The original code that was analyzed
    """
    has_leakage: bool
    leakage_issues: list[str]
    corrected_code: str
    original_code: str


def create_leakage_checker_agent(config: MLEStarConfig) -> Agent:
    """Create a Data Leakage Checker Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for leakage checking
    """
    return Agent(
        name="leakage_checker",
        system_prompt=LEAKAGE_CHECKER_SYSTEM_PROMPT,
        tools=[],
        model=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_leakage_check_prompt(code: str) -> str:
    """Build a prompt for the leakage checker agent.
    
    Args:
        code: The code to analyze for data leakage
        
    Returns:
        Formatted prompt string for the leakage checker agent
    """
    return f"""Analyze the following Python code for data leakage issues:

```python
{code}
```

Please:
1. Identify any data leakage issues in the preprocessing code
2. Explain each issue found
3. Provide the complete corrected code that fixes all leakage issues

If no leakage is found, respond with "NO_LEAKAGE_DETECTED" followed by the original code.

Format your response as:
ISSUES:
- [List each leakage issue found, or "None" if no issues]

CORRECTED_CODE:
```python
[Complete corrected code here]
```"""


def parse_leakage_check_response(response: str, original_code: str) -> LeakageCheckResult:
    """Parse the leakage checker agent's response.
    
    Args:
        response: The agent's response
        original_code: The original code that was analyzed
        
    Returns:
        LeakageCheckResult with parsed information
    """
    import re
    
    # Check if no leakage was detected
    if "NO_LEAKAGE_DETECTED" in response.upper():
        return LeakageCheckResult(
            has_leakage=False,
            leakage_issues=[],
            corrected_code=original_code,
            original_code=original_code,
        )
    
    # Extract issues
    issues = []
    issues_match = re.search(r'ISSUES:\s*(.*?)(?=CORRECTED_CODE:|```|$)', response, re.DOTALL | re.IGNORECASE)
    if issues_match:
        issues_text = issues_match.group(1).strip()
        # Parse bullet points
        issue_lines = re.findall(r'[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)', issues_text, re.DOTALL)
        issues = [issue.strip() for issue in issue_lines if issue.strip() and issue.strip().lower() != 'none']
    
    # Extract corrected code
    code_pattern = r'```(?:python)?\s*\n(.*?)```'
    code_matches = re.findall(code_pattern, response, re.DOTALL)
    
    if code_matches:
        # Use the last code block (usually the corrected code)
        corrected_code = code_matches[-1].strip()
    else:
        # No code block found, use original
        corrected_code = original_code
    
    has_leakage = len(issues) > 0 or corrected_code != original_code
    
    return LeakageCheckResult(
        has_leakage=has_leakage,
        leakage_issues=issues,
        corrected_code=corrected_code,
        original_code=original_code,
    )


async def check_for_leakage(
    code: str,
    config: MLEStarConfig,
    agent: Optional[Agent] = None,
) -> LeakageCheckResult:
    """Check code for data leakage and return corrected version if needed.
    
    Args:
        code: The code to analyze
        config: MLE-STAR configuration
        agent: Optional pre-created agent (creates new one if not provided)
        
    Returns:
        LeakageCheckResult with analysis and corrected code
    """
    if agent is None:
        agent = create_leakage_checker_agent(config)
    
    prompt = build_leakage_check_prompt(code)
    response = await agent.invoke_async(prompt)
    
    return parse_leakage_check_response(str(response), code)


def check_for_leakage_sync(
    code: str,
    config: MLEStarConfig,
    agent: Optional[Agent] = None,
) -> LeakageCheckResult:
    """Synchronous version of check_for_leakage.
    
    Args:
        code: The code to analyze
        config: MLE-STAR configuration
        agent: Optional pre-created agent
        
    Returns:
        LeakageCheckResult with analysis and corrected code
    """
    import asyncio
    return asyncio.run(check_for_leakage(code, config, agent))


def contains_leakage_patterns(code: str) -> list[str]:
    """Quick heuristic check for common leakage patterns in code.
    
    This is a fast pre-check that can identify obvious leakage patterns
    without invoking the LLM agent.
    
    Args:
        code: The code to check
        
    Returns:
        List of potential leakage patterns found
    """
    import re
    
    patterns = []
    
    # Pattern 1: Fitting on full data before split
    if re.search(r'\.fit\([^)]*\)\s*.*train_test_split', code, re.DOTALL):
        patterns.append("Possible fit before train/test split")
    
    # Pattern 2: StandardScaler/MinMaxScaler fit on full data
    scaler_fit = re.search(r'(StandardScaler|MinMaxScaler|RobustScaler)\(\)\.fit\((?!X_train|train)', code)
    if scaler_fit:
        patterns.append(f"Possible {scaler_fit.group(1)} fit on non-training data")
    
    # Pattern 3: Computing statistics on full dataset
    if re.search(r'(df|data|X)\[.*\]\.(mean|std|min|max)\(\).*(?:fillna|impute)', code, re.IGNORECASE):
        patterns.append("Possible imputation using full dataset statistics")
    
    # Pattern 4: LabelEncoder fit on full data
    if re.search(r'LabelEncoder\(\)\.fit\((?!.*train)', code):
        patterns.append("Possible LabelEncoder fit on non-training data")
    
    # Pattern 5: Target encoding without cross-validation
    if re.search(r'groupby.*mean.*(?:map|transform)', code) and 'fold' not in code.lower():
        patterns.append("Possible target encoding without cross-validation")
    
    return patterns
