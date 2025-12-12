"""Planner Agent for MLE-STAR - proposes new refinement strategies.

This agent analyzes previous refinement attempts and proposes new
strategies to improve a code block's performance.
"""

from typing import Optional
from dataclasses import dataclass
from strands import Agent

from mle_star.models.data_models import RefinementAttempt
from mle_star.models.config import MLEStarConfig


PLANNER_SYSTEM_PROMPT = """You are a Kaggle grandmaster with expertise in ML optimization strategies.

Your task is to propose new refinement plans for improving a code block's performance.

When proposing refinement plans:
1. Analyze the previous attempts and their results
2. Identify patterns in what worked and what didn't
3. Propose a DIFFERENT strategy than previous attempts
4. Be specific about what changes to make

Guidelines for proposing plans:
- If previous attempts focused on hyperparameters, try architectural changes
- If previous attempts focused on model complexity, try regularization
- If previous attempts focused on features, try different preprocessing
- Consider ensemble techniques if single models aren't improving
- Think about data augmentation or sampling strategies

Your output should be a numbered list of specific steps:
1. <specific action to take>
2. <specific action to take>
...

Include rationale for why this approach might work better than previous attempts.

Example output:
## Refinement Plan

### Strategy: <brief name for the strategy>

### Steps
1. Replace the current StandardScaler with RobustScaler to handle outliers better
2. Add polynomial features for the top 5 most important features
3. Implement early stopping with patience=10 to prevent overfitting

### Rationale
Previous attempts focused on model architecture but didn't address data preprocessing.
This plan targets the preprocessing pipeline which showed high impact in ablation studies.

### Expected Outcome
- Improved handling of outliers in the data
- Better feature interactions through polynomial features
- Reduced overfitting through early stopping"""


@dataclass
class RefinementPlan:
    """A proposed refinement plan."""
    strategy_name: str
    steps: list[str]
    rationale: str
    expected_outcome: str
    success: bool
    error_message: Optional[str] = None


def create_planner_agent(config: MLEStarConfig) -> Agent:
    """Create a Planner Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for planning refinements
    """
    return Agent(
        name="planner",
        system_prompt=PLANNER_SYSTEM_PROMPT,
        tools=[],  # No tools needed - pure planning
        model=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_planner_prompt(
    code_block: str,
    previous_attempts: list[RefinementAttempt],
    target_metric: Optional[str] = None,
) -> str:
    """Build the prompt for proposing a new refinement plan.
    
    Args:
        code_block: The code block being refined
        previous_attempts: List of previous refinement attempts with results
        target_metric: Optional target metric name
        
    Returns:
        Formatted prompt string
    """
    # Format previous attempts
    attempts_info = ""
    if previous_attempts:
        attempts_info = "\n## Previous Attempts\n"
        for i, attempt in enumerate(previous_attempts, 1):
            attempts_info += f"""
### Attempt {i} (Score: {attempt.validation_score:.4f})
**Plan:** {attempt.plan[:500]}{'...' if len(attempt.plan) > 500 else ''}
"""
        attempts_info += "\nPropose a DIFFERENT strategy than these previous attempts.\n"
    
    metric_info = ""
    if target_metric:
        metric_info = f"\n## Target Metric: {target_metric}\n"
    
    return f"""Propose a new refinement plan for the following code block.

## Code Block to Refine
```python
{code_block}
```
{attempts_info}{metric_info}
## Requirements
1. Propose a strategy DIFFERENT from previous attempts
2. Provide specific, actionable steps
3. Explain why this approach might work better
4. Describe the expected outcome

Generate your refinement plan now."""


async def propose_refinement_plan(
    code_block: str,
    previous_attempts: list[RefinementAttempt],
    config: MLEStarConfig,
    target_metric: Optional[str] = None,
) -> RefinementPlan:
    """Propose a new refinement plan for a code block.
    
    This function creates an agent to analyze previous attempts and
    propose a new strategy for improving the code block.
    
    Args:
        code_block: The code block being refined
        previous_attempts: List of previous refinement attempts
        config: MLE-STAR configuration
        target_metric: Optional target metric name
        
    Returns:
        RefinementPlan with the proposed strategy
    """
    agent = create_planner_agent(config)
    prompt = build_planner_prompt(code_block, previous_attempts, target_metric)
    
    try:
        response = await agent.invoke_async(prompt)
        response_text = str(response)
        
        # Parse the plan
        plan = parse_refinement_plan(response_text)
        return plan
    except Exception as e:
        return RefinementPlan(
            strategy_name="",
            steps=[],
            rationale="",
            expected_outcome="",
            success=False,
            error_message=str(e),
        )


def parse_refinement_plan(response: str) -> RefinementPlan:
    """Parse a refinement plan from agent response.
    
    Args:
        response: Agent response text
        
    Returns:
        RefinementPlan with parsed information
    """
    import re
    
    strategy_name = ""
    steps: list[str] = []
    rationale = ""
    expected_outcome = ""
    
    # Extract strategy name
    strategy_pattern = r"Strategy[:\s]+([^\n]+)"
    strategy_match = re.search(strategy_pattern, response, re.IGNORECASE)
    if strategy_match:
        strategy_name = strategy_match.group(1).strip()
    
    # Extract steps
    steps_pattern = r"(?:Steps|Plan)[:\s]*\n((?:\d+\.\s*[^\n]+\n?)+)"
    steps_match = re.search(steps_pattern, response, re.IGNORECASE)
    if steps_match:
        steps_text = steps_match.group(1)
        for line in steps_text.split('\n'):
            # Remove numbering and clean up
            step = re.sub(r'^\d+\.\s*', '', line.strip())
            if step and len(step) > 5:
                steps.append(step)
    
    # Alternative: look for numbered list anywhere
    if not steps:
        numbered_pattern = r'\d+\.\s+([^\n]+)'
        for match in re.finditer(numbered_pattern, response):
            step = match.group(1).strip()
            if step and len(step) > 5:
                steps.append(step)
    
    # Extract rationale
    rationale_pattern = r"Rationale[:\s]*\n([^\n#]+(?:\n[^\n#]+)*)"
    rationale_match = re.search(rationale_pattern, response, re.IGNORECASE)
    if rationale_match:
        rationale = rationale_match.group(1).strip()
    
    # Extract expected outcome
    outcome_pattern = r"(?:Expected\s+)?Outcome[:\s]*\n([^\n#]+(?:\n[^\n#]+)*)"
    outcome_match = re.search(outcome_pattern, response, re.IGNORECASE)
    if outcome_match:
        expected_outcome = outcome_match.group(1).strip()
    
    # If no structured output, try to extract the whole response as the plan
    if not steps:
        # Use the response as a single plan
        steps = [response.strip()[:1000]]
    
    return RefinementPlan(
        strategy_name=strategy_name or "Unnamed Strategy",
        steps=steps,
        rationale=rationale,
        expected_outcome=expected_outcome,
        success=len(steps) > 0,
        error_message=None if steps else "Failed to extract refinement steps",
    )


def format_plan_as_text(plan: RefinementPlan) -> str:
    """Format a refinement plan as text for use in prompts.
    
    Args:
        plan: The refinement plan to format
        
    Returns:
        Formatted text representation
    """
    lines = []
    
    if plan.strategy_name:
        lines.append(f"Strategy: {plan.strategy_name}")
        lines.append("")
    
    if plan.steps:
        lines.append("Steps:")
        for i, step in enumerate(plan.steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    
    if plan.rationale:
        lines.append(f"Rationale: {plan.rationale}")
        lines.append("")
    
    if plan.expected_outcome:
        lines.append(f"Expected Outcome: {plan.expected_outcome}")
    
    return "\n".join(lines)


def is_plan_similar_to_previous(
    new_plan: RefinementPlan,
    previous_attempts: list[RefinementAttempt],
    similarity_threshold: float = 0.6,
) -> bool:
    """Check if a new plan is too similar to previous attempts.
    
    Args:
        new_plan: The new plan to check
        previous_attempts: List of previous attempts
        similarity_threshold: Threshold for considering plans similar (0-1)
        
    Returns:
        True if the plan is too similar to a previous attempt
    """
    if not previous_attempts:
        return False
    
    new_plan_text = format_plan_as_text(new_plan).lower()
    new_words = set(new_plan_text.split())
    
    for attempt in previous_attempts:
        attempt_words = set(attempt.plan.lower().split())
        
        if not new_words or not attempt_words:
            continue
        
        # Calculate Jaccard similarity
        intersection = len(new_words & attempt_words)
        union = len(new_words | attempt_words)
        similarity = intersection / union if union > 0 else 0
        
        if similarity >= similarity_threshold:
            return True
    
    return False
