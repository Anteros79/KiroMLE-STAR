"""Extractor Agent for MLE-STAR - identifies most impactful code blocks.

This agent analyzes ablation summaries to identify the code block with the
most significant performance impact and generates an initial refinement plan.
"""

from typing import Optional
from dataclasses import dataclass
from strands import Agent

from mle_star.models.data_models import SolutionState
from mle_star.models.config import MLEStarConfig
from mle_star.models.model_factory import create_model
from mle_star.agents.summarizer import AblationSummary


EXTRACTOR_SYSTEM_PROMPT = """You are a code analyst who identifies the most impactful code regions for targeted improvement.

<objective>
Extract the exact code block corresponding to the most impactful component and create a detailed refinement plan.
</objective>

<extraction_rules>
1. MATCH: Map the component name from ablation summary to actual code region
2. COMPLETE: Include the entire logical unit (full function, class, or code section)
3. DEPENDENCIES: Note any imports or variables the block depends on
4. BOUNDARIES: Don't split functions or classes mid-way
</extraction_rules>

<block_identification>
A valid code block should be:
- SELF-CONTAINED: Can be understood without full solution context
- MODIFIABLE: Changes won't break unrelated pipeline sections
- TESTABLE: Can verify improvement independently
- SIGNIFICANT: Large enough to contain meaningful logic
</block_identification>

<skip_logic>
If the most impactful component was ALREADY REFINED (in refined_blocks list):
1. Document why the top choice was skipped
2. Select the NEXT most impactful UNREFINED component
3. Continue down the ranking until finding an unrefined block
4. If all high-impact blocks are refined, select a medium-impact one
</skip_logic>

<refinement_planning>
For the extracted block, create a detailed plan:
1. WHAT: Specific modifications to make (line-level changes)
2. WHY: Theoretical basis for why this should improve performance
3. HOW: Concrete implementation steps
4. EXPECTED GAIN: Quantitative estimate of improvement
5. RISKS: What could go wrong and how to mitigate
</refinement_planning>

<output_format>
## Extracted Code Block

### Target Component
- Name: {component_name}
- Impact: {impact_value:+.6f}
- Selection Reason: {why this component was chosen}
- Previously Refined: No

### Code Block
```python
{exact code from solution - complete logical unit}
```

### Dependencies
- Imports: {list of required imports}
- Variables: {external variables used}

### Refinement Plan
1. {specific_step_1}
2. {specific_step_2}
3. {specific_step_3}

### Expected Outcome
- Current Impact: {current_delta}
- Target Improvement: {expected_gain}
- Confidence: {high/medium/low}
- Rationale: {why this plan should work}
</output_format>"""


@dataclass
class ExtractedBlock:
    """Result of code block extraction."""
    component_name: str
    code_block: str
    impact: float
    refinement_plan: str
    expected_improvement: float
    success: bool
    error_message: Optional[str] = None


def create_extractor_agent(config: MLEStarConfig) -> Agent:
    """Create an Extractor Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for code block extraction
    """
    return Agent(
        name="extractor",
        system_prompt=EXTRACTOR_SYSTEM_PROMPT,
        tools=[],  # No tools needed - pure analysis
        model=create_model(config),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_extraction_prompt(
    solution_state: SolutionState,
    ablation_summary: AblationSummary,
) -> str:
    """Build the prompt for extracting a code block.
    
    Args:
        solution_state: Current solution state with code and history
        ablation_summary: Summary of ablation study results
        
    Returns:
        Formatted prompt string
    """
    # Build list of previously refined blocks
    refined_blocks_info = ""
    if solution_state.refined_blocks:
        refined_blocks_info = "\n## Previously Refined Blocks (DO NOT SELECT THESE)\n"
        for i, block in enumerate(solution_state.refined_blocks, 1):
            preview = block[:150].replace('\n', ' ') + "..." if len(block) > 150 else block
            refined_blocks_info += f"{i}. {preview}\n"
        refined_blocks_info += "\nPrioritize blocks that have NOT been refined yet.\n"
    
    # Format component impacts
    impacts_info = ""
    if ablation_summary.component_impacts:
        impacts_info = "\n### Component Impacts (from ablation study)\n"
        sorted_impacts = sorted(
            ablation_summary.component_impacts.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        for name, impact in sorted_impacts:
            impacts_info += f"- {name}: {impact:+.4f}\n"
    
    return f"""Extract the most impactful code block from the solution and generate a refinement plan.

## Ablation Summary
- Baseline Score: {ablation_summary.baseline_score}
- Most Impactful Component: {ablation_summary.most_impactful_component}
- Impact: {ablation_summary.most_impactful_delta:+.4f}
{impacts_info}

### Insights
{chr(10).join('- ' + insight for insight in ablation_summary.insights) if ablation_summary.insights else '- No specific insights available'}
{refined_blocks_info}

## Current Solution
```python
{solution_state.current_code}
```

## Requirements
1. Identify the code block corresponding to the most impactful component
2. If that block was already refined, select the next most impactful unrefined block
3. Extract the exact code block from the solution
4. Generate a specific refinement plan with actionable steps

Provide your extraction in the structured format specified."""


async def extract_code_block(
    solution_state: SolutionState,
    ablation_summary: AblationSummary,
    config: MLEStarConfig,
) -> ExtractedBlock:
    """Extract the most impactful code block for refinement.
    
    This function creates an agent to identify and extract the code block
    with the most significant performance impact, prioritizing unrefined blocks.
    
    Args:
        solution_state: Current solution state
        ablation_summary: Summary of ablation study results
        config: MLE-STAR configuration
        
    Returns:
        ExtractedBlock with code and refinement plan
    """
    agent = create_extractor_agent(config)
    prompt = build_extraction_prompt(solution_state, ablation_summary)
    
    try:
        response = await agent.invoke_async(prompt)
        response_text = str(response)
        
        # Parse the extraction result
        extracted = parse_extraction_result(response_text, ablation_summary)
        return extracted
    except Exception as e:
        return ExtractedBlock(
            component_name="",
            code_block="",
            impact=0.0,
            refinement_plan="",
            expected_improvement=0.0,
            success=False,
            error_message=str(e),
        )


def parse_extraction_result(
    response: str,
    ablation_summary: AblationSummary,
) -> ExtractedBlock:
    """Parse extraction result from agent response.
    
    Args:
        response: Agent response text
        ablation_summary: Original ablation summary for reference
        
    Returns:
        ExtractedBlock with parsed information
    """
    import re
    
    component_name = ""
    code_block = ""
    impact = 0.0
    refinement_plan = ""
    expected_improvement = 0.0
    
    # Extract component name
    name_pattern = r"(?:Target\s+)?Component[:\s]*\n.*?Name[:\s]*([^\n]+)"
    name_match = re.search(name_pattern, response, re.IGNORECASE | re.DOTALL)
    if name_match:
        component_name = name_match.group(1).strip()
    
    # Alternative: look for "Name:" directly
    if not component_name:
        alt_name_pattern = r"Name[:\s]+([^\n]+)"
        alt_match = re.search(alt_name_pattern, response, re.IGNORECASE)
        if alt_match:
            component_name = alt_match.group(1).strip()
    
    # Extract code block
    code_pattern = r"```(?:python)?\s*\n(.*?)```"
    code_matches = re.findall(code_pattern, response, re.DOTALL)
    if code_matches:
        # Use the first substantial code block (likely the extracted block)
        for match in code_matches:
            if len(match.strip()) > 20:
                code_block = match.strip()
                break
    
    # Extract impact
    impact_pattern = r"Impact[:\s]*([-+]?\d*\.?\d+)"
    impact_match = re.search(impact_pattern, response, re.IGNORECASE)
    if impact_match:
        try:
            impact = float(impact_match.group(1))
        except ValueError:
            pass
    
    # If no impact found, use from ablation summary
    if impact == 0.0 and component_name:
        # Try to find matching component in ablation summary
        for comp_name, comp_impact in ablation_summary.component_impacts.items():
            if comp_name.lower() in component_name.lower() or component_name.lower() in comp_name.lower():
                impact = comp_impact
                break
    
    # Extract refinement plan
    plan_pattern = r"(?:Initial\s+)?Refinement\s+Plan[:\s]*\n((?:\d+\.\s*[^\n]+\n?)+)"
    plan_match = re.search(plan_pattern, response, re.IGNORECASE)
    if plan_match:
        refinement_plan = plan_match.group(1).strip()
    
    # Alternative: look for numbered list after "Plan"
    if not refinement_plan:
        alt_plan_pattern = r"Plan[:\s]*\n((?:[-*\d]+\.?\s*[^\n]+\n?)+)"
        alt_plan_match = re.search(alt_plan_pattern, response, re.IGNORECASE)
        if alt_plan_match:
            refinement_plan = alt_plan_match.group(1).strip()
    
    # Extract expected improvement
    improvement_pattern = r"(?:Target|Expected)\s+[Ii]mprovement[:\s]*([-+]?\d*\.?\d+)"
    improvement_match = re.search(improvement_pattern, response, re.IGNORECASE)
    if improvement_match:
        try:
            expected_improvement = float(improvement_match.group(1))
        except ValueError:
            pass
    
    return ExtractedBlock(
        component_name=component_name,
        code_block=code_block,
        impact=impact,
        refinement_plan=refinement_plan,
        expected_improvement=expected_improvement,
        success=bool(code_block and refinement_plan),
        error_message=None if (code_block and refinement_plan) else "Failed to extract code block or plan",
    )


def should_skip_block(
    block: str,
    refined_blocks: list[str],
    similarity_threshold: float = 0.8,
) -> bool:
    """Check if a code block should be skipped because it was already refined.
    
    Args:
        block: The code block to check
        refined_blocks: List of previously refined blocks
        similarity_threshold: Threshold for considering blocks similar (0-1)
        
    Returns:
        True if the block should be skipped
    """
    if not refined_blocks:
        return False
    
    block_normalized = _normalize_code(block)
    
    for refined in refined_blocks:
        refined_normalized = _normalize_code(refined)
        similarity = _calculate_similarity(block_normalized, refined_normalized)
        if similarity >= similarity_threshold:
            return True
    
    return False


def _normalize_code(code: str) -> str:
    """Normalize code for comparison by removing whitespace and comments."""
    import re
    
    # Remove comments
    code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    # Remove docstrings
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
    # Normalize whitespace
    code = ' '.join(code.split())
    return code.lower()


def _calculate_similarity(s1: str, s2: str) -> float:
    """Calculate similarity between two strings using Jaccard similarity."""
    if not s1 or not s2:
        return 0.0
    
    # Use word-level tokens
    tokens1 = set(s1.split())
    tokens2 = set(s2.split())
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    
    return intersection / union if union > 0 else 0.0
