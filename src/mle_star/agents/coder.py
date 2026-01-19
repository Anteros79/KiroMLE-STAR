"""Coder Agent for MLE-STAR - implements refinement plans.

This agent takes a code block and a refinement plan, then implements
the plan to produce a refined version of the code block.
"""

from typing import Optional
from dataclasses import dataclass
from strands import Agent

from mle_star.models.config import MLEStarConfig
from mle_star.models.model_factory import create_model


CODER_SYSTEM_PROMPT = """You are a precise ML engineer who implements refinement plans with surgical accuracy.

<objective>
Implement the refinement plan on the code block while preserving all working functionality and maintaining code quality.
</objective>

<implementation_principles>
1. MINIMAL CHANGES: Only modify what the plan explicitly requires
2. PRESERVE INTERFACE: Keep function/class signatures unchanged unless plan specifies otherwise
3. BACKWARD COMPATIBLE: Ensure refined code integrates seamlessly with existing pipeline
4. WELL-DOCUMENTED: Add comments explaining significant changes
5. DEFENSIVE: Handle edge cases and potential errors
</implementation_principles>

<code_quality_standards>
- Syntactically correct Python (no syntax errors)
- Proper indentation (4 spaces, consistent)
- All variables defined before use
- All imports available (use standard ML libraries)
- Handle edge cases: empty data, NaN values, single-class scenarios
- No hardcoded paths or magic numbers without comments
</code_quality_standards>

<change_tracking>
Add inline comments for ALL significant changes:
```python
# REFINED: [description of change and why]
new_code_here  # was: old_code_here
```

Example:
```python
# REFINED: Changed to RobustScaler for better outlier handling
scaler = RobustScaler()  # was: StandardScaler()

# REFINED: Added polynomial features for top predictors
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X[top_features])
```
</change_tracking>

<validation_checklist>
Before outputting, verify:
□ All plan steps are implemented
□ No syntax errors
□ All imports are included
□ Variable names are consistent
□ Code is properly indented
□ Edge cases are handled
□ Changes are documented with comments
</validation_checklist>

<output_format>
Return ONLY the refined code block wrapped in ```python``` markers.
Do NOT include explanations outside the code block.
The code must be DIRECTLY SUBSTITUTABLE for the original block.

```python
# REFINED: [summary of changes]
[complete refined code here]
```
</output_format>

<thinking>
Before implementing, verify:
- Do I understand each step of the plan?
- What's the minimal change needed?
- Are there any edge cases to handle?
- Will this integrate with the rest of the pipeline?
</thinking>"""


@dataclass
class RefinedCodeBlock:
    """Result of code refinement."""
    original_code: str
    refined_code: str
    changes_made: list[str]
    success: bool
    error_message: Optional[str] = None


def create_coder_agent(config: MLEStarConfig) -> Agent:
    """Create a Coder Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for code refinement
    """
    return Agent(
        name="coder",
        system_prompt=CODER_SYSTEM_PROMPT,
        tools=[],  # No tools needed - pure code generation
        model=create_model(config),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def build_coder_prompt(
    code_block: str,
    refinement_plan: str,
    context: Optional[str] = None,
) -> str:
    """Build the prompt for implementing a refinement plan.
    
    Args:
        code_block: The original code block to refine
        refinement_plan: The plan describing how to refine the code
        context: Optional additional context about the solution
        
    Returns:
        Formatted prompt string
    """
    context_section = ""
    if context:
        context_section = f"\n## Additional Context\n{context}\n"
    
    return f"""Implement the following refinement plan on the given code block.

## Original Code Block
```python
{code_block}
```

## Refinement Plan
{refinement_plan}
{context_section}
## Requirements
1. Implement ALL steps in the refinement plan
2. Return ONLY the refined code block
3. Ensure the code is syntactically correct
4. Maintain compatibility with the original interface

Output the refined code block now."""


async def refine_code_block(
    code_block: str,
    refinement_plan: str,
    config: MLEStarConfig,
    context: Optional[str] = None,
) -> RefinedCodeBlock:
    """Refine a code block according to a plan.
    
    This function creates an agent to implement the refinement plan
    and produce an improved version of the code block.
    
    Args:
        code_block: The original code block to refine
        refinement_plan: The plan describing how to refine the code
        config: MLE-STAR configuration
        context: Optional additional context
        
    Returns:
        RefinedCodeBlock with the refined code
    """
    agent = create_coder_agent(config)
    prompt = build_coder_prompt(code_block, refinement_plan, context)
    
    try:
        response = await agent.invoke_async(prompt)
        response_text = str(response)
        
        # Extract the refined code
        refined_code = extract_code_from_response(response_text)
        
        if not refined_code:
            return RefinedCodeBlock(
                original_code=code_block,
                refined_code="",
                changes_made=[],
                success=False,
                error_message="Failed to extract refined code from response",
            )
        
        # Identify changes made
        changes = identify_changes(code_block, refined_code)
        
        return RefinedCodeBlock(
            original_code=code_block,
            refined_code=refined_code,
            changes_made=changes,
            success=True,
        )
    except Exception as e:
        return RefinedCodeBlock(
            original_code=code_block,
            refined_code="",
            changes_made=[],
            success=False,
            error_message=str(e),
        )


def extract_code_from_response(response: str) -> str:
    """Extract Python code from agent response.
    
    Args:
        response: Agent response text
        
    Returns:
        Extracted code or empty string
    """
    import re
    
    # Look for code blocks
    code_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_pattern, response, re.DOTALL)
    
    if matches:
        # Return the longest code block (likely the main implementation)
        return max(matches, key=len).strip()
    
    # If no code blocks, try to extract indented code
    lines = response.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        if line.startswith('    ') or line.startswith('\t'):
            code_lines.append(line)
            in_code = True
        elif in_code and line.strip() == '':
            code_lines.append(line)
        elif in_code and not line.startswith(' ') and line.strip():
            break
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return ""


def identify_changes(original: str, refined: str) -> list[str]:
    """Identify the changes made between original and refined code.
    
    Args:
        original: Original code block
        refined: Refined code block
        
    Returns:
        List of change descriptions
    """
    changes = []
    
    # Simple line-based diff
    original_lines = set(original.strip().split('\n'))
    refined_lines = set(refined.strip().split('\n'))
    
    added = refined_lines - original_lines
    removed = original_lines - refined_lines
    
    if added:
        changes.append(f"Added {len(added)} new lines")
    if removed:
        changes.append(f"Removed {len(removed)} lines")
    
    # Check for specific patterns
    if 'import' in refined and 'import' not in original:
        changes.append("Added new imports")
    
    if refined.count('def ') > original.count('def '):
        changes.append("Added new functions")
    
    if refined.count('class ') > original.count('class '):
        changes.append("Added new classes")
    
    # Check for common improvements
    if 'try:' in refined and 'try:' not in original:
        changes.append("Added error handling")
    
    if 'logging' in refined.lower() and 'logging' not in original.lower():
        changes.append("Added logging")
    
    if not changes:
        changes.append("Minor modifications")
    
    return changes


def substitute_code_block(
    full_solution: str,
    original_block: str,
    refined_block: str,
) -> str:
    """Substitute a refined code block into the full solution.
    
    Args:
        full_solution: The complete solution code
        original_block: The original code block to replace
        refined_block: The refined code block to insert
        
    Returns:
        Updated solution with the refined block
    """
    # Try exact replacement first
    if original_block in full_solution:
        return full_solution.replace(original_block, refined_block, 1)
    
    # Try normalized replacement (handle whitespace differences)
    original_normalized = _normalize_whitespace(original_block)
    
    # Find the block in the solution
    lines = full_solution.split('\n')
    solution_text = '\n'.join(lines)
    
    # Try to find a fuzzy match
    start_idx = _find_fuzzy_match(solution_text, original_block)
    
    if start_idx >= 0:
        # Find the end of the original block
        end_idx = start_idx + len(original_block)
        
        # Adjust for whitespace
        while end_idx < len(solution_text) and solution_text[end_idx] in ' \t\n':
            end_idx += 1
        
        return solution_text[:start_idx] + refined_block + solution_text[end_idx:]
    
    # If no match found, append the refined block (fallback)
    return full_solution + "\n\n# Refined block (could not locate original):\n" + refined_block


def _normalize_whitespace(code: str) -> str:
    """Normalize whitespace in code for comparison."""
    lines = code.split('\n')
    normalized = []
    for line in lines:
        # Preserve indentation structure but normalize spaces
        stripped = line.rstrip()
        if stripped:
            normalized.append(stripped)
    return '\n'.join(normalized)


def _find_fuzzy_match(text: str, pattern: str, threshold: float = 0.7) -> int:
    """Find a fuzzy match for a pattern in text.
    
    Args:
        text: Text to search in
        pattern: Pattern to find
        threshold: Similarity threshold (0-1)
        
    Returns:
        Start index of match, or -1 if not found
    """
    pattern_lines = pattern.strip().split('\n')
    text_lines = text.split('\n')
    
    if not pattern_lines:
        return -1
    
    # Look for the first line of the pattern
    first_line = pattern_lines[0].strip()
    
    for i, line in enumerate(text_lines):
        if first_line in line or line.strip() == first_line:
            # Found potential start, check if rest matches
            match_score = _calculate_block_similarity(
                '\n'.join(text_lines[i:i+len(pattern_lines)]),
                pattern
            )
            if match_score >= threshold:
                # Calculate character position
                return sum(len(l) + 1 for l in text_lines[:i])
    
    return -1


def _calculate_block_similarity(block1: str, block2: str) -> float:
    """Calculate similarity between two code blocks."""
    lines1 = set(line.strip() for line in block1.split('\n') if line.strip())
    lines2 = set(line.strip() for line in block2.split('\n') if line.strip())
    
    if not lines1 or not lines2:
        return 0.0
    
    intersection = len(lines1 & lines2)
    union = len(lines1 | lines2)
    
    return intersection / union if union > 0 else 0.0
