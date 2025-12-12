"""Property-based tests for ablation study component impact capture.

Feature: mle-star-agent, Property 5: Ablation study captures component impacts
Validates: Requirements 5.2, 5.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck

from mle_star.agents.ablation_study import parse_ablation_results, AblationResult
from mle_star.agents.summarizer import parse_ablation_summary, AblationSummary


# Strategy for generating valid component names (alphanumeric with underscores)
# Use a more efficient approach: start with a letter, then allow letters/underscores, end with a letter
_letters = st.sampled_from("abcdefghijklmnopqrstuvwxyz")
_letters_and_underscores = st.sampled_from("abcdefghijklmnopqrstuvwxyz_")

component_name_strategy = st.builds(
    lambda first, middle, last: first + middle + last,
    first=_letters,
    middle=st.text(alphabet=_letters_and_underscores, min_size=1, max_size=20),
    last=_letters,
)

# Strategy for generating valid scores (reasonable ML metric values)
score_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Strategy for generating impact values (can be positive or negative)
impact_strategy = st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)


def generate_ablation_output(baseline: float, components: dict[str, float]) -> str:
    """Generate a well-formed ablation study output string.
    
    Args:
        baseline: Baseline performance score
        components: Dict mapping component names to their impact values
        
    Returns:
        Formatted ablation output string
    """
    lines = ["Ablation Results:"]
    lines.append(f"- Baseline: {baseline:.4f}")
    
    for name, impact in components.items():
        score = baseline - impact  # Score when component is removed
        lines.append(f"- Without {name}: {score:.4f} (impact: {impact:.4f})")
    
    return "\n".join(lines)


def generate_summary_output(baseline: float, components: dict[str, float]) -> str:
    """Generate a well-formed ablation summary output string.
    
    Args:
        baseline: Baseline performance score
        components: Dict mapping component names to their impact values
        
    Returns:
        Formatted summary output string
    """
    lines = ["## Ablation Summary", "", "### Baseline Performance"]
    lines.append(f"- Score: {baseline:.4f}")
    lines.append("")
    lines.append("### Component Impacts (sorted by impact)")
    
    # Sort by absolute impact
    sorted_components = sorted(components.items(), key=lambda x: abs(x[1]), reverse=True)
    
    for i, (name, impact) in enumerate(sorted_components, 1):
        direction = "decreases" if impact > 0 else "increases"
        lines.append(f"{i}. {name}: Impact = {impact:.4f} (removing this {direction} performance)")
    
    if sorted_components:
        most_impactful = sorted_components[0]
        lines.append("")
        lines.append("### Most Impactful Component")
        lines.append(f"- Component: {most_impactful[0]}")
        lines.append(f"- Impact: {most_impactful[1]:.4f}")
        lines.append("- Recommendation: Consider improving this component")
    
    lines.append("")
    lines.append("### Key Insights")
    lines.append("- The ablation study identified key components")
    lines.append("- Performance varies with component modifications")
    
    return "\n".join(lines)


class TestAblationResultsParsing:
    """Property tests for parse_ablation_results function.
    
    Feature: mle-star-agent, Property 5: Ablation study captures component impacts
    Validates: Requirements 5.2
    """
    
    @given(
        baseline=score_strategy,
        components=st.dictionaries(
            keys=component_name_strategy,
            values=impact_strategy,
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_ablation_results_capture_all_component_impacts(
        self, baseline: float, components: dict[str, float]
    ):
        """Property 5: For any ablation output with components, parsing captures all impacts.
        
        Feature: mle-star-agent, Property 5: Ablation study captures component impacts
        Validates: Requirements 5.2
        """
        # Filter out empty component names
        components = {k: v for k, v in components.items() if k.strip()}
        assume(len(components) >= 1)
        
        # Generate well-formed ablation output
        ablation_output = generate_ablation_output(baseline, components)
        
        # Parse the results
        parsed_baseline, parsed_impacts = parse_ablation_results(ablation_output)
        
        # Property: baseline score is captured
        assert abs(parsed_baseline - baseline) < 0.001, \
            f"Baseline not captured correctly: expected {baseline}, got {parsed_baseline}"
        
        # Property: all component impacts are captured
        assert len(parsed_impacts) == len(components), \
            f"Not all components captured: expected {len(components)}, got {len(parsed_impacts)}"
        
        # Property: each component's impact is captured correctly
        for name, expected_impact in components.items():
            assert name in parsed_impacts, f"Component '{name}' not found in parsed results"
            actual_impact = parsed_impacts[name]
            assert abs(actual_impact - expected_impact) < 0.001, \
                f"Impact for '{name}' incorrect: expected {expected_impact}, got {actual_impact}"


class TestAblationSummaryParsing:
    """Property tests for parse_ablation_summary function.
    
    Feature: mle-star-agent, Property 5: Ablation study captures component impacts
    Validates: Requirements 5.3
    """
    
    @given(
        baseline=score_strategy,
        components=st.dictionaries(
            keys=component_name_strategy,
            values=impact_strategy,
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=100)
    def test_summary_identifies_most_impactful_component(
        self, baseline: float, components: dict[str, float]
    ):
        """Property 5: For any summary with components, the most impactful is identified.
        
        Feature: mle-star-agent, Property 5: Ablation study captures component impacts
        Validates: Requirements 5.3
        """
        # Filter out empty component names
        components = {k: v for k, v in components.items() if k.strip()}
        assume(len(components) >= 1)
        
        # Generate well-formed summary output
        summary_output = generate_summary_output(baseline, components)
        
        # Parse the summary
        summary: AblationSummary = parse_ablation_summary(summary_output)
        
        # Property: summary is successful when components exist
        assert summary.success, f"Summary parsing failed: {summary.error_message}"
        
        # Property: most impactful component is identified
        assert summary.most_impactful_component, "Most impactful component not identified"
        
        # Property: the identified component has the largest absolute impact
        expected_most_impactful = max(components.keys(), key=lambda k: abs(components[k]))
        assert summary.most_impactful_component == expected_most_impactful, \
            f"Wrong most impactful: expected '{expected_most_impactful}', got '{summary.most_impactful_component}'"
