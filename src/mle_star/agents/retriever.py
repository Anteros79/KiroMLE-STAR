"""Retriever Agent for MLE-STAR - searches web for effective ML models.

This agent uses web search to find state-of-the-art models for a given ML task
and returns structured ModelCandidate objects.
"""

from typing import Optional
from strands import Agent, tool

from mle_star.models.data_models import TaskDescription, ModelCandidate
from mle_star.models.config import MLEStarConfig
from mle_star.models.model_factory import create_model
from mle_star.tools.web_search import web_search, WebSearchResponse


RETRIEVER_SYSTEM_PROMPT = """You are a Kaggle grandmaster with extensive experience in machine learning competitions.

Your task is to search for state-of-the-art models that could be effective for the given ML task.

When searching for models:
1. Consider the task type (classification, regression, etc.)
2. Consider the data modality (tabular, image, text, audio)
3. Look for proven approaches that have won competitions or achieved top results
4. Prioritize models with available Python implementations

For each model you find, provide:
- Model name
- Description of the approach and why it's suitable
- Example code showing how to implement and train the model

Return your findings in a structured format that can be parsed into ModelCandidate objects."""


@tool
def search_models(query: str, num_results: int = 4) -> str:
    """Search the web for ML models and approaches.
    
    Args:
        query: Search query for finding ML models (e.g., "best tabular classification model kaggle")
        num_results: Number of results to return (default: 4)
        
    Returns:
        Formatted string with search results containing model information
    """
    response: WebSearchResponse = web_search(query=query, num_results=num_results)
    
    if not response.success:
        return f"Search failed: {response.error_message}"
    
    if not response.results:
        return "No results found for the query."
    
    # Format results for the agent
    formatted_results = []
    for i, result in enumerate(response.results, 1):
        formatted_results.append(
            f"Result {i}:\n"
            f"  Title: {result.title}\n"
            f"  URL: {result.url}\n"
            f"  Description: {result.snippet}\n"
            f"  Model Name: {result.model_name or 'Unknown'}"
        )
    
    return "\n\n".join(formatted_results)


def create_retriever_agent(config: MLEStarConfig) -> Agent:
    """Create a Retriever Agent configured with the given settings.
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Configured Strands Agent for model retrieval
    """
    return Agent(
        name="retriever",
        system_prompt=RETRIEVER_SYSTEM_PROMPT,
        tools=[search_models],
        model=create_model(config),
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def parse_model_candidates_from_response(response: str) -> list[ModelCandidate]:
    """Parse ModelCandidate objects from agent response text.
    
    This function attempts to extract structured model information from
    the agent's free-form response.
    
    Args:
        response: The agent's response text containing model information
        
    Returns:
        List of ModelCandidate objects extracted from the response
    """
    candidates = []
    
    # Split response into sections (each model typically separated by blank lines or headers)
    sections = _split_into_model_sections(response)
    
    for section in sections:
        candidate = _parse_single_candidate(section)
        if candidate:
            candidates.append(candidate)
    
    return candidates


def _split_into_model_sections(text: str) -> list[str]:
    """Split response text into individual model sections.
    
    Args:
        text: Full response text
        
    Returns:
        List of text sections, each describing one model
    """
    import re
    
    # Try to split by numbered sections (1., 2., etc.) or model headers
    patterns = [
        r'(?=\n\d+\.\s+)',  # Numbered list
        r'(?=\n#{1,3}\s+)',  # Markdown headers
        r'(?=\nModel\s*\d*:)',  # "Model:" or "Model 1:" headers
        r'(?=\n\*\*[^*]+\*\*)',  # Bold headers
    ]
    
    for pattern in patterns:
        sections = re.split(pattern, text)
        sections = [s.strip() for s in sections if s.strip()]
        if len(sections) > 1:
            return sections
    
    # If no clear sections, try splitting by double newlines
    sections = text.split('\n\n')
    sections = [s.strip() for s in sections if s.strip() and len(s) > 50]
    
    if sections:
        return sections
    
    # Return the whole text as one section
    return [text] if text.strip() else []


def _parse_single_candidate(section: str) -> Optional[ModelCandidate]:
    """Parse a single ModelCandidate from a text section.
    
    Args:
        section: Text describing a single model
        
    Returns:
        ModelCandidate if parsing successful, None otherwise
    """
    import re
    
    if not section or len(section) < 20:
        return None
    
    # Extract model name
    name = _extract_model_name(section)
    if not name:
        return None
    
    # Extract description
    description = _extract_description(section)
    
    # Extract code example
    example_code = _extract_code_example(section)
    
    return ModelCandidate(
        name=name,
        description=description,
        example_code=example_code,
    )


def _extract_model_name(text: str) -> str:
    """Extract model name from text section.
    
    Args:
        text: Text section describing a model
        
    Returns:
        Extracted model name or empty string
    """
    import re
    
    # Try various patterns to extract model name
    patterns = [
        r'(?:Model|Name)[:\s]+([A-Za-z0-9_\-\s]+?)(?:\n|$)',
        r'\*\*([A-Za-z0-9_\-\s]+?)\*\*',
        r'^#+\s*([A-Za-z0-9_\-\s]+?)(?:\n|$)',
        r'^\d+\.\s*([A-Za-z0-9_\-\s]+?)(?:\n|:)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up the name
            name = re.sub(r'\s+', ' ', name)
            if len(name) > 2 and len(name) < 100:
                return name
    
    # Fallback: use first line if it looks like a name
    first_line = text.split('\n')[0].strip()
    first_line = re.sub(r'^[\d\.\*#\-]+\s*', '', first_line)
    if len(first_line) > 2 and len(first_line) < 100:
        return first_line[:100]
    
    return "Unknown Model"


def _extract_description(text: str) -> str:
    """Extract model description from text section.
    
    Args:
        text: Text section describing a model
        
    Returns:
        Extracted description
    """
    import re
    
    # Try to find explicit description
    patterns = [
        r'(?:Description|About|Overview)[:\s]+(.+?)(?=\n\n|Code|Example|```|$)',
        r'(?:suitable for|works well|effective for|designed for)(.+?)(?=\n\n|Code|Example|```|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            desc = match.group(1).strip()
            if len(desc) > 20:
                return desc[:500]
    
    # Fallback: use text before any code block
    code_start = text.find('```')
    if code_start > 50:
        return text[:code_start].strip()[:500]
    
    # Use first paragraph
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        para = para.strip()
        if len(para) > 30 and '```' not in para:
            return para[:500]
    
    return text[:500] if text else "No description available"


def _extract_code_example(text: str) -> str:
    """Extract code example from text section.
    
    Args:
        text: Text section describing a model
        
    Returns:
        Extracted code example or empty string
    """
    import re
    
    # Look for code blocks
    code_pattern = r'```(?:python)?\s*\n(.*?)```'
    matches = re.findall(code_pattern, text, re.DOTALL)
    
    if matches:
        # Return the longest code block (likely the main implementation)
        return max(matches, key=len).strip()
    
    # Look for indented code blocks
    lines = text.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        if line.startswith('    ') or line.startswith('\t'):
            code_lines.append(line)
            in_code = True
        elif in_code and line.strip() == '':
            code_lines.append(line)
        elif in_code:
            break
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return ""


async def retrieve_models(
    task: TaskDescription,
    config: MLEStarConfig,
) -> list[ModelCandidate]:
    """Retrieve model candidates for a given ML task.
    
    This is the main entry point for the retriever functionality.
    It creates an agent, searches for models, and returns structured candidates.
    
    Args:
        task: The ML task description
        config: MLE-STAR configuration
        
    Returns:
        List of ModelCandidate objects (up to num_retrieved_models)
    """
    agent = create_retriever_agent(config)
    
    # Construct the search prompt
    prompt = f"""Search for the best ML models for the following task:

Task Type: {task.task_type}
Data Modality: {task.data_modality}
Evaluation Metric: {task.evaluation_metric}
Description: {task.description}

Please search for {config.num_retrieved_models} effective models that could solve this task.
For each model, provide:
1. Model name
2. Description of why it's suitable
3. Example Python code for implementation

Focus on models that have proven effective in competitions or real-world applications."""

    # Invoke the agent
    response = await agent.invoke_async(prompt)
    response_text = str(response)
    
    # Parse the response into ModelCandidate objects
    candidates = parse_model_candidates_from_response(response_text)
    
    # Limit to configured number
    return candidates[:config.num_retrieved_models]
