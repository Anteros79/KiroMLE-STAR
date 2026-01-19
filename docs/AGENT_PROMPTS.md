# MLE-STAR Agent System Prompts

## Overview

This document describes the system prompts for all 14 agents in the MLE-STAR pipeline, including the design rationale and optimization strategies for each.

The prompts have been optimized for use with **Qwen3 Next 72B** running on a local llama.cpp server (Lemonade), but are designed to work well with any capable LLM.

## Design Principles

All agent prompts follow these core principles:

1. **Structured Output**: XML-style tags and explicit output formats ensure reliable parsing
2. **Thinking Sections**: `<thinking>` blocks leverage the model's reasoning capabilities
3. **Explicit Checklists**: Concrete verification steps reduce errors
4. **Error Handling**: Clear guidance on failure modes and fallbacks
5. **Differentiation Logic**: Planners explicitly check for novelty vs previous attempts
6. **Code Examples**: Templates show expected patterns

---

## Phase 1: Initial Solution Agents

### 1. Retriever Agent

**Purpose**: Search the web for state-of-the-art ML models suitable for the task.

**Key Improvements**:
- Added structured search strategy (competitions → papers → implementations)
- Explicit evaluation criteria with prioritization
- Structured output format with suitability scores
- Thinking section for task analysis before searching

**Rationale**: The original prompt was too generic. By adding explicit search priorities and output structure, we get more consistent, parseable results and better model recommendations.

```
Location: src/mle_star/agents/retriever.py
```

### 2. Candidate Evaluator Agent

**Purpose**: Generate and execute code to evaluate each model candidate.

**Key Improvements**:
- Explicit evaluation protocol with numbered steps
- Metric interpretation guidance (higher vs lower is better)
- Error handling with fallback to baseline models
- Code requirements checklist (random seeds, imports, etc.)

**Rationale**: Evaluation consistency is critical. The improved prompt ensures reproducible results with proper random seeds, standardized output format, and graceful error handling.

```
Location: src/mle_star/agents/candidate_evaluator.py
```

### 3. Merger Agent

**Purpose**: Combine multiple model solutions into an ensemble.

**Key Improvements**:
- Detailed ensemble strategies for both regression and classification
- Diversity check before merging
- Explicit merge decision rules (when to merge, skip, or stop)
- Thinking section for diversity analysis

**Rationale**: Not all models benefit from ensembling. The improved prompt adds diversity assessment and clear decision rules to avoid wasting computation on low-value merges.

```
Location: src/mle_star/agents/merger.py
```

### 4. Leakage Checker Agent

**Purpose**: Detect and correct data leakage in preprocessing code.

**Key Improvements**:
- Categorized leakage types with examples
- Detection patterns checklist
- Before/after code examples showing correct patterns
- Structured output format for issues and corrections

**Rationale**: Data leakage is subtle and common. The improved prompt provides concrete patterns to look for and explicit correction templates, reducing false negatives.

```
Location: src/mle_star/agents/leakage_checker.py
```

### 5. Data Usage Checker Agent

**Purpose**: Ensure all provided data files are utilized in the solution.

**Key Improvements**:
- File type purposes guide (what each file type typically contains)
- Integration strategies with code examples
- Merge checklist (keys, types, missing values)
- Warnings about leakage when adding external data

**Rationale**: Unused data often contains valuable signal. The improved prompt provides concrete integration patterns and warns about common pitfalls.

```
Location: src/mle_star/agents/data_usage_checker.py
```

---

## Phase 2: Iterative Refinement Agents

### 6. Ablation Study Agent

**Purpose**: Identify which pipeline components contribute most to performance.

**Key Improvements**:
- Component identification taxonomy (6 categories)
- Explicit ablation methodology (baseline → ablate → measure → calculate)
- Structured output format for reliable parsing
- Exploration guidance for subsequent iterations

**Rationale**: Ablation studies guide refinement. The improved prompt ensures systematic component identification and consistent output format for downstream parsing.

```
Location: src/mle_star/agents/ablation_study.py
```

### 7. Summarizer Agent

**Purpose**: Parse ablation results and extract actionable insights.

**Key Improvements**:
- Four-part analysis framework (quantitative, ranking, direction, actionable)
- Insight generation with WHY/HOW/RISK analysis
- Structured output with markdown tables
- Priority recommendations for next steps

**Rationale**: Raw ablation output needs interpretation. The improved prompt transforms numbers into strategic recommendations with clear priorities.

```
Location: src/mle_star/agents/summarizer.py
```

### 8. Extractor Agent

**Purpose**: Identify the most impactful code block for targeted refinement.

**Key Improvements**:
- Extraction rules for complete logical units
- Block boundary guidelines (self-contained, modifiable, testable)
- Skip logic for already-refined blocks
- Detailed refinement planning with expected outcomes

**Rationale**: Extracting the right code block is critical. The improved prompt ensures complete logical units are extracted and provides clear skip logic for iterative refinement.

```
Location: src/mle_star/agents/extractor.py
```

### 9. Planner Agent

**Purpose**: Propose novel refinement strategies different from previous attempts.

**Key Improvements**:
- Eight orthogonal strategy categories
- Explicit differentiation protocol (5-step verification)
- Structured plan with theoretical basis
- Risk assessment and fallback plans

**Rationale**: Avoiding repetition is key to exploration. The improved prompt forces explicit differentiation analysis and provides diverse strategy categories to choose from.

```
Location: src/mle_star/agents/planner.py
```

### 10. Coder Agent

**Purpose**: Implement refinement plans with surgical precision.

**Key Improvements**:
- Implementation principles (minimal changes, preserve interface)
- Code quality standards checklist
- Change tracking with inline comments
- Validation checklist before output

**Rationale**: Implementation errors waste iterations. The improved prompt emphasizes minimal changes, proper documentation, and explicit validation.

```
Location: src/mle_star/agents/coder.py
```

### 11. Debugger Agent

**Purpose**: Analyze error tracebacks and fix code.

**Key Improvements**:
- Systematic diagnosis process (5 steps)
- Error category taxonomy with fix patterns
- Fix principles (minimal, preserve, defensive)
- Learning from history for repeated failures

**Rationale**: Debugging is iterative. The improved prompt provides systematic diagnosis, categorized fixes, and explicit guidance for learning from failed attempts.

```
Location: src/mle_star/agents/debugger.py
```

---

## Phase 3: Ensemble Agents

### 12. Ensemble Planner Agent

**Purpose**: Propose strategies for combining multiple solutions.

**Key Improvements**:
- Comprehensive strategy catalog (averaging, voting, stacking, blending)
- Diversity analysis framework
- Strategy selection matrix based on diversity and task type
- Differentiation from previous attempts

**Rationale**: Ensemble strategy selection depends on model diversity. The improved prompt provides a decision matrix and explicit diversity analysis.

```
Location: src/mle_star/agents/ensemble_planner.py
```

### 13. Ensembler Agent

**Purpose**: Implement the proposed ensemble strategy.

**Key Improvements**:
- Implementation protocol with numbered steps
- Code patterns for each ensemble type
- Validation protocol comparing to individual models
- Sanity checks before finalizing

**Rationale**: Ensemble implementation has many pitfalls. The improved prompt provides code templates and explicit validation steps.

```
Location: src/mle_star/agents/ensembler.py
```

### 14. Submission Agent

**Purpose**: Generate production-ready submission files.

**Key Improvements**:
- Subsampling removal checklist (8 patterns)
- Test data handling template
- Submission format validation checklist
- Final checks with statistics output

**Rationale**: Submission errors are costly. The improved prompt provides explicit patterns to remove and validation steps to catch format issues.

```
Location: src/mle_star/agents/submission.py
```

---

## Prompt Structure Conventions

All prompts use consistent XML-style sections:

```
<objective>
Clear statement of the agent's goal
</objective>

<section_name>
Detailed guidance for this aspect
</section_name>

<output_format>
Exact format expected in response
</output_format>

<thinking>
Questions to consider before responding
</thinking>
```

This structure:
1. Helps the model organize its response
2. Makes prompts easier to maintain
3. Enables consistent parsing of outputs
4. Leverages chain-of-thought reasoning

---

## Configuration

Default model configuration (in `src/mle_star/models/config.py`):

```python
model_id: str = "qwen3-next-72b"
model_provider: str = "lemonade"
lemonade_base_url: str = "http://localhost:8080"
temperature: float = 0.7
max_tokens: int = 4096
```

The prompts are optimized for Qwen3's instruction-following capabilities but work with other models by adjusting temperature and max_tokens as needed.

---

## Testing Prompts

To test individual agent prompts:

```python
from mle_star.agents.retriever import create_retriever_agent
from mle_star.models.config import MLEStarConfig

config = MLEStarConfig()
agent = create_retriever_agent(config)

response = await agent.invoke_async("Search for models for tabular classification")
print(response)
```

---

## Maintenance

When updating prompts:

1. Test with representative tasks before deploying
2. Verify output parsing still works
3. Update this documentation
4. Consider backward compatibility with saved runs

---

## References

- MLE-STAR Paper: Google DeepMind research on ML engineering agents
- Strands Agents SDK: Framework for building AI agents
- Qwen3 Documentation: Model capabilities and best practices
