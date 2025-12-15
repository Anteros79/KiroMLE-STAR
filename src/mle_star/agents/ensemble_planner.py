"""Ensemble Planner Agent for MLE-STAR - proposes ensemble strategies.

This agent analyzes multiple solutions and proposes strategies to combine
them into a more powerful ensemble. It uses previous ensemble attempts
as feedback to propose improved strategies.
"""

from typing import Optional
from dataclasses import dataclass
from strands import Agent

from mle_star.models.data_models import EnsembleResult
from mle_star.models.config import MLEStarConfig
from mle_star.models.model_factory import create_model


ENSEMBLE_PLANNER_SYSTEM_PROMPT = """You are a Kaggle grandmaster with extensive experience in ensemble methods.

Your task is to propose ensemble strategies to combine multiple ML solutions into a single, more powerful solution.

When proposing ensemble strategies, consider:
1. Simple averaging of predictions (for regression or probability outputs)
2. Weighted averaging with optimized weights based on validation performance
3. Voting (majority or soft voting for classification)
4. Stacking with a meta-learner (e.g., logistic regression, gradient boosting)
5. Blending with a holdout set
6. Rank averaging for ranking tasks

Guidelines for proposing strategies:
- Start with simpler strategies before complex ones
- Consider the diversity of the base models
- Account for the task type (classification vs regression)
- Use validation performance to guide weight assignment
- Avoid overfitting the ensemble to the validation set

Your output should follow this format:

## Ensemble Strategy

### Strategy Name: <brief name>

### Description
<detailed description of the ensemble approach>

### Implementation Steps
1. <specific step>
2. <specific step>
...

### Weight Assignment (if applicable)
<how to assign weights to each model>

### Expected Benefit
<why this strategy might improve performance>

Use previous ensemble attempts as feedback to propose DIFFERENT strategies."""


@dataclass
class EnsemblePlan:
    """A proposed ensemble strategy plan."""
    strategy_name: str
    description: str
    implementation_steps: list[str]
    weight_assignment: Optional[str]
    expected_benefit: str
    success: bool
    error_message: Optional[str] = None


def create_ensemble_planner_agent(config: MLEStarConfig) -> Agent:
    """Create an Ensemble Planner Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for ensemble planning
    """
    return Agent(
        name="ensemble_planner",
        system_prompt=ENSEMBLE_PLANNER_SYSTEM_PROMPT,
        tools=[],  # No tools needed - pure planning
        model=create_model(config),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_ensemble_planner_prompt(
    solutions: list[tuple[str, float]],
    task_type: str,
    evaluation_metric: str,
    previous_attempts: list[EnsembleResult],
) -> str:
    """Build the prompt for proposing an ensemble strategy.
    
    Args:
        solutions: List of (solution_code, validation_score) tuples
        task_type: Type of ML task (classification, regression, etc.)
        evaluation_metric: Metric used for evaluation
        previous_attempts: List of previous ensemble attempts with results
        
    Returns:
        Formatted prompt string
    """
    # Format solutions info
    solutions_info = "\n## Available Solutions\n"
    for i, (code, score) in enumerate(solutions, 1):
        # Truncate code for prompt
        code_preview = code[:500] + "..." if len(code) > 500 else code
        solutions_info += f"""
### Solution {i} (Score: {score:.4f})
```python
{code_preview}
```
"""
    
    # Format previous attempts
    attempts_info = ""
    if previous_attempts:
        attempts_info = "\n## Previous Ensemble Attempts\n"
        for i, attempt in enumerate(previous_attempts, 1):
            attempts_info += f"""
### Attempt {i}: {attempt.strategy} (Score: {attempt.validation_score:.4f})
"""
        attempts_info += "\nPropose a DIFFERENT strategy than these previous attempts.\n"
    
    return f"""Propose an ensemble strategy to combine the following ML solutions.

## Task Information
- Task Type: {task_type}
- Evaluation Metric: {evaluation_metric}
- Number of Solutions: {len(solutions)}
{solutions_info}{attempts_info}
## Requirements
1. Propose a strategy appropriate for the task type
2. Consider the validation scores when assigning weights
3. Provide specific implementation steps
4. Explain the expected benefit

Generate your ensemble strategy proposal now."""


async def propose_ensemble_strategy(
    solutions: list[tuple[str, float]],
    task_type: str,
    evaluation_metric: str,
    previous_attempts: list[EnsembleResult],
    config: MLEStarConfig,
) -> EnsemblePlan:
    """Propose an ensemble strategy to combine multiple solutions.
    
    This function creates an agent to analyze the available solutions
    and propose a strategy for combining them.
    
    Args:
        solutions: List of (solution_code, validation_score) tuples
        task_type: Type of ML task
        evaluation_metric: Metric used for evaluation
        previous_attempts: List of previous ensemble attempts
        config: MLE-STAR configuration
        
    Returns:
        EnsemblePlan with the proposed strategy
    """
    agent = create_ensemble_planner_agent(config)
    prompt = build_ensemble_planner_prompt(
        solutions, task_type, evaluation_metric, previous_attempts
    )
    
    try:
        response = await agent.invoke_async(prompt)
        response_text = str(response)
        
        # Parse the plan
        plan = parse_ensemble_plan(response_text)
        return plan
    except Exception as e:
        return EnsemblePlan(
            strategy_name="",
            description="",
            implementation_steps=[],
            weight_assignment=None,
            expected_benefit="",
            success=False,
            error_message=str(e),
        )


def parse_ensemble_plan(response: str) -> EnsemblePlan:
    """Parse an ensemble plan from agent response.
    
    Args:
        response: Agent response text
        
    Returns:
        EnsemblePlan with parsed information
    """
    import re
    
    strategy_name = ""
    description = ""
    implementation_steps: list[str] = []
    weight_assignment: Optional[str] = None
    expected_benefit = ""
    
    # Extract strategy name
    name_pattern = r"Strategy\s+Name[:\s]+([^\n]+)"
    name_match = re.search(name_pattern, response, re.IGNORECASE)
    if name_match:
        strategy_name = name_match.group(1).strip()
    
    # Extract description
    desc_pattern = r"Description[:\s]*\n([^\n#]+(?:\n[^\n#]+)*)"
    desc_match = re.search(desc_pattern, response, re.IGNORECASE)
    if desc_match:
        description = desc_match.group(1).strip()
    
    # Extract implementation steps
    steps_pattern = r"(?:Implementation\s+)?Steps[:\s]*\n((?:\d+\.\s*[^\n]+\n?)+)"
    steps_match = re.search(steps_pattern, response, re.IGNORECASE)
    if steps_match:
        steps_text = steps_match.group(1)
        for line in steps_text.split('\n'):
            step = re.sub(r'^\d+\.\s*', '', line.strip())
            if step and len(step) > 5:
                implementation_steps.append(step)
    
    # Alternative: look for numbered list anywhere
    if not implementation_steps:
        numbered_pattern = r'\d+\.\s+([^\n]+)'
        for match in re.finditer(numbered_pattern, response):
            step = match.group(1).strip()
            if step and len(step) > 5:
                implementation_steps.append(step)
    
    # Extract weight assignment
    weight_pattern = r"Weight\s+Assignment[:\s]*\n([^\n#]+(?:\n[^\n#]+)*)"
    weight_match = re.search(weight_pattern, response, re.IGNORECASE)
    if weight_match:
        weight_assignment = weight_match.group(1).strip()
    
    # Extract expected benefit
    benefit_pattern = r"Expected\s+Benefit[:\s]*\n([^\n#]+(?:\n[^\n#]+)*)"
    benefit_match = re.search(benefit_pattern, response, re.IGNORECASE)
    if benefit_match:
        expected_benefit = benefit_match.group(1).strip()
    
    # If no structured output, use the response as description
    if not strategy_name and not implementation_steps:
        strategy_name = "Custom Ensemble"
        description = response.strip()[:500]
        implementation_steps = [response.strip()[:1000]]
    
    return EnsemblePlan(
        strategy_name=strategy_name or "Unnamed Strategy",
        description=description,
        implementation_steps=implementation_steps,
        weight_assignment=weight_assignment,
        expected_benefit=expected_benefit,
        success=len(implementation_steps) > 0,
        error_message=None if implementation_steps else "Failed to extract implementation steps",
    )


def format_ensemble_plan_as_text(plan: EnsemblePlan) -> str:
    """Format an ensemble plan as text for use in prompts.
    
    Args:
        plan: The ensemble plan to format
        
    Returns:
        Formatted text representation
    """
    lines = []
    
    if plan.strategy_name:
        lines.append(f"Strategy: {plan.strategy_name}")
        lines.append("")
    
    if plan.description:
        lines.append(f"Description: {plan.description}")
        lines.append("")
    
    if plan.implementation_steps:
        lines.append("Implementation Steps:")
        for i, step in enumerate(plan.implementation_steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    
    if plan.weight_assignment:
        lines.append(f"Weight Assignment: {plan.weight_assignment}")
        lines.append("")
    
    if plan.expected_benefit:
        lines.append(f"Expected Benefit: {plan.expected_benefit}")
    
    return "\n".join(lines)


def is_strategy_similar_to_previous(
    new_plan: EnsemblePlan,
    previous_attempts: list[EnsembleResult],
    similarity_threshold: float = 0.6,
) -> bool:
    """Check if a new strategy is too similar to previous attempts.
    
    Args:
        new_plan: The new plan to check
        previous_attempts: List of previous attempts
        similarity_threshold: Threshold for considering strategies similar (0-1)
        
    Returns:
        True if the strategy is too similar to a previous attempt
    """
    if not previous_attempts:
        return False
    
    new_plan_text = format_ensemble_plan_as_text(new_plan).lower()
    new_words = set(new_plan_text.split())
    
    for attempt in previous_attempts:
        attempt_words = set(attempt.strategy.lower().split())
        
        if not new_words or not attempt_words:
            continue
        
        # Calculate Jaccard similarity
        intersection = len(new_words & attempt_words)
        union = len(new_words | attempt_words)
        similarity = intersection / union if union > 0 else 0
        
        if similarity >= similarity_threshold:
            return True
    
    return False
