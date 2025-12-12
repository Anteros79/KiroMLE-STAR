"""Summarization Agent for MLE-STAR - parses ablation study output.

This agent analyzes ablation study results and extracts component impact
information to guide the refinement process.
"""

from typing import Optional
from dataclasses import dataclass
from strands import Agent

from mle_star.models.config import MLEStarConfig


SUMMARIZATION_SYSTEM_PROMPT = """You are an expert at analyzing ML experiments and extracting insights.

Your task is to parse ablation study output and summarize the impact of each component.

When summarizing ablation results:
1. Identify the baseline performance
2. List each component that was tested
3. Calculate and report the impact of each component (how much performance changes when removed)
4. Identify which component has the MOST SIGNIFICANT effect on performance
5. Provide actionable insights for improvement

Your summary should be structured as follows:
## Ablation Summary

### Baseline Performance
- Score: <baseline_score>

### Component Impacts (sorted by impact)
1. <component_name>: Impact = <delta> (removing this <increases/decreases> performance)
2. ...

### Most Impactful Component
- Component: <name>
- Impact: <delta>
- Recommendation: <brief suggestion for improvement>

### Key Insights
- <insight 1>
- <insight 2>
...

Be precise with numbers and clear about which components matter most."""


@dataclass
class AblationSummary:
    """Structured summary of ablation study results."""
    baseline_score: float
    component_impacts: dict[str, float]  # component_name -> impact
    most_impactful_component: str
    most_impactful_delta: float
    insights: list[str]
    raw_summary: str
    success: bool
    error_message: Optional[str] = None


def create_summarization_agent(config: MLEStarConfig) -> Agent:
    """Create a Summarization Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for summarization
    """
    return Agent(
        name="summarizer",
        system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
        tools=[],  # No tools needed - pure text analysis
        model=config.model_id,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_summarization_prompt(ablation_output: str) -> str:
    """Build the prompt for summarizing ablation results.
    
    Args:
        ablation_output: Raw output from ablation study execution
        
    Returns:
        Formatted prompt string
    """
    return f"""Analyze the following ablation study output and provide a structured summary.

## Ablation Study Output
{ablation_output}

## Requirements
1. Extract the baseline performance score
2. List all components that were tested and their impacts
3. Identify the component with the MOST SIGNIFICANT impact
4. Provide actionable insights for improvement

Please provide your summary in the structured format specified."""


async def summarize_ablation_results(
    ablation_output: str,
    config: MLEStarConfig,
) -> AblationSummary:
    """Summarize ablation study results.
    
    This function creates an agent to analyze ablation output and extract
    structured insights about component impacts.
    
    Args:
        ablation_output: Raw output from ablation study
        config: MLE-STAR configuration
        
    Returns:
        AblationSummary with structured insights
    """
    agent = create_summarization_agent(config)
    prompt = build_summarization_prompt(ablation_output)
    
    try:
        response = await agent.invoke_async(prompt)
        response_text = str(response)
        
        # Parse the summary
        summary = parse_ablation_summary(response_text)
        return summary
    except Exception as e:
        return AblationSummary(
            baseline_score=0.0,
            component_impacts={},
            most_impactful_component="",
            most_impactful_delta=0.0,
            insights=[],
            raw_summary="",
            success=False,
            error_message=str(e),
        )


def parse_ablation_summary(response: str) -> AblationSummary:
    """Parse structured summary from agent response.
    
    Args:
        response: Agent response text containing the summary
        
    Returns:
        AblationSummary with extracted information
    """
    import re
    
    baseline_score = 0.0
    component_impacts: dict[str, float] = {}
    most_impactful_component = ""
    most_impactful_delta = 0.0
    insights: list[str] = []
    
    # Extract baseline score
    baseline_pattern = r"(?:Baseline|Score)[:\s]*([-+]?\d*\.?\d+)"
    baseline_match = re.search(baseline_pattern, response, re.IGNORECASE)
    if baseline_match:
        try:
            baseline_score = float(baseline_match.group(1))
        except ValueError:
            pass
    
    # Extract component impacts
    # Pattern: "<component_name>: Impact = <delta>"
    impact_pattern = r"(\w[\w\s]*?)[:\s]+Impact\s*=\s*([-+]?\d*\.?\d+)"
    for match in re.finditer(impact_pattern, response, re.IGNORECASE):
        component_name = match.group(1).strip()
        try:
            impact = float(match.group(2))
            component_impacts[component_name] = impact
        except ValueError:
            continue
    
    # Alternative pattern: numbered list with impact
    if not component_impacts:
        alt_pattern = r"\d+\.\s*([^:]+)[:\s]*([-+]?\d*\.?\d+)"
        for match in re.finditer(alt_pattern, response):
            component_name = match.group(1).strip()
            if len(component_name) > 2 and len(component_name) < 100:
                try:
                    impact = float(match.group(2))
                    component_impacts[component_name] = impact
                except ValueError:
                    continue
    
    # Extract most impactful component
    most_impactful_pattern = r"Most\s+Impactful\s+Component[:\s]*\n.*?Component[:\s]*([^\n]+)"
    most_match = re.search(most_impactful_pattern, response, re.IGNORECASE | re.DOTALL)
    if most_match:
        most_impactful_component = most_match.group(1).strip()
    
    # If not found explicitly, determine from impacts
    if not most_impactful_component and component_impacts:
        # Find component with largest absolute impact
        most_impactful_component = max(
            component_impacts.keys(),
            key=lambda k: abs(component_impacts[k])
        )
        most_impactful_delta = component_impacts[most_impactful_component]
    
    # Extract impact for most impactful component
    if most_impactful_component:
        impact_for_most_pattern = rf"{re.escape(most_impactful_component)}.*?Impact[:\s]*([-+]?\d*\.?\d+)"
        impact_match = re.search(impact_for_most_pattern, response, re.IGNORECASE)
        if impact_match:
            try:
                most_impactful_delta = float(impact_match.group(1))
            except ValueError:
                pass
        elif most_impactful_component in component_impacts:
            most_impactful_delta = component_impacts[most_impactful_component]
    
    # Extract insights
    insights_pattern = r"(?:Key\s+)?Insights?[:\s]*\n((?:[-*]\s*[^\n]+\n?)+)"
    insights_match = re.search(insights_pattern, response, re.IGNORECASE)
    if insights_match:
        insights_text = insights_match.group(1)
        for line in insights_text.split('\n'):
            line = re.sub(r'^[-*]\s*', '', line.strip())
            if line and len(line) > 5:
                insights.append(line)
    
    return AblationSummary(
        baseline_score=baseline_score,
        component_impacts=component_impacts,
        most_impactful_component=most_impactful_component,
        most_impactful_delta=most_impactful_delta,
        insights=insights,
        raw_summary=response,
        success=bool(most_impactful_component),
        error_message=None if most_impactful_component else "Could not identify most impactful component",
    )
