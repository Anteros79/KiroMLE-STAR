"""Ablation Study Agent for MLE-STAR - identifies component impacts.

This agent generates and executes ablation study code to evaluate the
contribution of individual ML components by modifying or disabling them.
"""

from typing import Optional
from dataclasses import dataclass
from strands import Agent, tool

from mle_star.models.data_models import TaskDescription, SolutionState
from mle_star.models.config import MLEStarConfig
from mle_star.models.model_factory import create_model
from mle_star.tools.execute_python import execute_python, ExecutionResult


ABLATION_STUDY_SYSTEM_PROMPT = """You are an ML diagnostician who systematically identifies which pipeline components drive model performance.

<objective>
Generate and execute Python code that performs a rigorous ablation study, measuring the contribution of each distinct component.
</objective>

<component_identification>
Identify and categorize these component types in the solution:
1. PREPROCESSING: Scaling (StandardScaler, MinMaxScaler), encoding (OneHot, Label), imputation
2. FEATURE_ENGINEERING: Derived features, polynomial features, interactions, aggregations
3. FEATURE_SELECTION: SelectKBest, RFE, importance-based selection
4. MODEL_ARCHITECTURE: Model type, layer sizes, tree depths, ensemble size
5. REGULARIZATION: Dropout, L1/L2 penalties, early stopping, max_depth limits
6. HYPERPARAMETERS: Learning rate, batch size, n_estimators, C/gamma values
</component_identification>

<ablation_methodology>
For each identified component:
1. BASELINE: Run the full pipeline, record validation score
2. ABLATE: Remove or simplify the component to a naive baseline
   - Scaling → No scaling (raw features)
   - Feature engineering → Remove derived features
   - Feature selection → Use all features
   - Complex model → Simple baseline (LogisticRegression, DecisionTree)
   - Regularization → Remove regularization
3. MEASURE: Run ablated pipeline with same train/val split
4. CALCULATE: impact = baseline_score - ablated_score
   - Positive impact = component HELPS performance
   - Negative impact = component HURTS performance (removing it improves score)
</ablation_methodology>

<output_format>
Print results in this EXACT format (parseable):
```
Ablation Results:
- Baseline: {score:.6f}
- Without {component_1}: {score:.6f} (impact: {delta:+.6f})
- Without {component_2}: {score:.6f} (impact: {delta:+.6f})
- Without {component_3}: {score:.6f} (impact: {delta:+.6f})
Most Impactful: {component_name} (impact: {delta:+.6f})
```
</output_format>

<exploration_guidance>
If previous ablation summaries exist:
- Explore DIFFERENT components than those already studied
- Focus on components with uncertain or unstudied impacts
- Consider interactions between components
</exploration_guidance>

<code_requirements>
- Use same random_state=42 for all experiments
- Each ablation must be independent (reset state between runs)
- Handle errors gracefully (report -inf for failed ablations)
- Target 3-5 distinct components per study
</code_requirements>"""


@dataclass
class AblationResult:
    """Result of an ablation study."""
    baseline_score: float
    component_impacts: dict[str, float]  # component_name -> impact (delta from baseline)
    raw_output: str
    success: bool
    error_message: Optional[str] = None


@tool
def run_ablation_code(code: str, timeout: int = 600) -> str:
    """Execute ablation study Python code and return the results.
    
    Args:
        code: Python code for ablation study to execute
        timeout: Maximum execution time in seconds (default: 600 for longer studies)
        
    Returns:
        Execution results including ablation study output
    """
    result: ExecutionResult = execute_python(code=code, timeout=timeout)
    
    output_parts = []
    
    if result.success:
        output_parts.append("Ablation study execution successful!")
    else:
        output_parts.append(f"Execution failed with return code: {result.return_code}")
    
    if result.stdout:
        output_parts.append(f"\nStdout:\n{result.stdout}")
    
    if result.stderr:
        output_parts.append(f"\nStderr:\n{result.stderr}")
    
    if result.error_message:
        output_parts.append(f"\nError: {result.error_message}")
    
    return "\n".join(output_parts)


def create_ablation_study_agent(config: MLEStarConfig) -> Agent:
    """Create an Ablation Study Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for ablation studies
    """
    return Agent(
        name="ablation_study",
        system_prompt=ABLATION_STUDY_SYSTEM_PROMPT,
        tools=[run_ablation_code],
        model=create_model(config),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_ablation_prompt(
    task: TaskDescription,
    solution_state: SolutionState,
) -> str:
    """Build the prompt for generating an ablation study.
    
    Args:
        task: The ML task description
        solution_state: Current solution state with code and history
        
    Returns:
        Formatted prompt string
    """
    previous_summaries = ""
    if solution_state.ablation_summaries:
        previous_summaries = "\n\n## Previous Ablation Summaries\n"
        for i, summary in enumerate(solution_state.ablation_summaries, 1):
            previous_summaries += f"\n### Iteration {i}:\n{summary}\n"
        previous_summaries += "\nPlease explore DIFFERENT parts of the pipeline than those already studied."
    
    refined_blocks_info = ""
    if solution_state.refined_blocks:
        refined_blocks_info = "\n\n## Previously Refined Blocks\n"
        refined_blocks_info += "The following code blocks have already been refined:\n"
        for block in solution_state.refined_blocks:
            # Show first 100 chars of each block for context
            preview = block[:100].replace('\n', ' ') + "..." if len(block) > 100 else block
            refined_blocks_info += f"- {preview}\n"
    
    return f"""Generate Python code to perform an ablation study on the following ML solution.

## Task Information
- Task Type: {task.task_type}
- Data Modality: {task.data_modality}
- Evaluation Metric: {task.evaluation_metric}
- Dataset Path: {task.dataset_path}

## Current Solution (Validation Score: {solution_state.validation_score})
```python
{solution_state.current_code}
```
{previous_summaries}{refined_blocks_info}

## Requirements
1. Identify 3-5 distinct ML components in the solution
2. For each component, create a variation that disables or simplifies it
3. Run each variation and measure validation performance
4. Print results in this exact format:
   Ablation Results:
   - Baseline: <score>
   - Without <component_name>: <score> (impact: <delta>)
   ...

Generate the ablation study code and execute it using run_ablation_code."""


async def run_ablation_study(
    task: TaskDescription,
    solution_state: SolutionState,
    config: MLEStarConfig,
) -> AblationResult:
    """Run an ablation study on the current solution.
    
    This function creates an agent, generates ablation study code, executes it,
    and returns structured results about component impacts.
    
    Args:
        task: The ML task description
        solution_state: Current solution state
        config: MLE-STAR configuration
        
    Returns:
        AblationResult with component impacts
    """
    agent = create_ablation_study_agent(config)
    prompt = build_ablation_prompt(task, solution_state)
    
    try:
        response = await agent.invoke_async(prompt)
        response_text = str(response)
        
        # Parse the ablation results
        baseline_score, component_impacts = parse_ablation_results(response_text)
        
        return AblationResult(
            baseline_score=baseline_score,
            component_impacts=component_impacts,
            raw_output=response_text,
            success=len(component_impacts) > 0,
            error_message=None if component_impacts else "Failed to parse ablation results",
        )
    except Exception as e:
        return AblationResult(
            baseline_score=0.0,
            component_impacts={},
            raw_output="",
            success=False,
            error_message=str(e),
        )


def parse_ablation_results(response: str) -> tuple[float, dict[str, float]]:
    """Parse ablation study results from agent response.
    
    Args:
        response: Agent response text containing ablation results
        
    Returns:
        Tuple of (baseline_score, component_impacts dict)
    """
    import re
    
    baseline_score = 0.0
    component_impacts: dict[str, float] = {}
    
    # Look for baseline score
    baseline_pattern = r"Baseline[:\s]*([-+]?\d*\.?\d+)"
    baseline_match = re.search(baseline_pattern, response, re.IGNORECASE)
    if baseline_match:
        try:
            baseline_score = float(baseline_match.group(1))
        except ValueError:
            pass
    
    # Look for component impacts
    # Pattern: "Without <component>: <score> (impact: <delta>)"
    impact_pattern = r"Without\s+([^:]+)[:\s]*([-+]?\d*\.?\d+)\s*\(impact[:\s]*([-+]?\d*\.?\d+)\)"
    for match in re.finditer(impact_pattern, response, re.IGNORECASE):
        component_name = match.group(1).strip()
        try:
            impact = float(match.group(3))
            component_impacts[component_name] = impact
        except ValueError:
            continue
    
    # Alternative pattern without explicit impact
    # Pattern: "Without <component>: <score>"
    if not component_impacts:
        alt_pattern = r"Without\s+([^:]+)[:\s]*([-+]?\d*\.?\d+)"
        for match in re.finditer(alt_pattern, response, re.IGNORECASE):
            component_name = match.group(1).strip()
            try:
                score = float(match.group(2))
                # Calculate impact as difference from baseline
                impact = baseline_score - score
                component_impacts[component_name] = impact
            except ValueError:
                continue
    
    return baseline_score, component_impacts
