"""Web search tool for model retrieval in MLE-STAR agents."""

import os
import json
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


@dataclass
class SearchResult:
    """A single search result with model information."""
    title: str
    url: str
    snippet: str
    model_name: Optional[str] = None
    description: Optional[str] = None
    example_code: Optional[str] = None


@dataclass
class WebSearchResponse:
    """Response from web search containing multiple results."""
    results: list[SearchResult] = field(default_factory=list)
    query: str = ""
    success: bool = False
    error_message: Optional[str] = None


def _extract_model_info(result: dict) -> SearchResult:
    """Extract model information from a raw search result.
    
    Args:
        result: Raw search result dictionary
        
    Returns:
        SearchResult with extracted information
    """
    title = result.get("title", "")
    url = result.get("link", result.get("url", ""))
    snippet = result.get("snippet", result.get("description", ""))
    
    # Try to extract model name from title
    model_name = title.split("-")[0].strip() if "-" in title else title.split(":")[0].strip()
    
    return SearchResult(
        title=title,
        url=url,
        snippet=snippet,
        model_name=model_name,
        description=snippet,
        example_code=None  # Code examples would need to be fetched from the URL
    )


def web_search(
    query: str,
    num_results: int = 4,
    api_key: Optional[str] = None,
    search_engine_id: Optional[str] = None
) -> WebSearchResponse:
    """Search the web for ML models and approaches.
    
    This function supports Google Custom Search API. If API credentials are not
    provided, it will attempt to read from environment variables:
    - GOOGLE_API_KEY: Google API key
    - GOOGLE_SEARCH_ENGINE_ID: Custom Search Engine ID
    
    Args:
        query: Search query for finding ML models
        num_results: Number of results to return (default: 4)
        api_key: Google API key (optional, reads from env if not provided)
        search_engine_id: Google Custom Search Engine ID (optional)
        
    Returns:
        WebSearchResponse containing search results
    """
    # Get API credentials from environment if not provided
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    search_engine_id = search_engine_id or os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
    
    if not api_key or not search_engine_id:
        return WebSearchResponse(
            results=[],
            query=query,
            success=False,
            error_message="Missing API credentials. Set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables."
        )
    
    try:
        # Build the Google Custom Search API URL
        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "num": min(num_results, 10)  # Google API max is 10
        }
        url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
        
        # Make the request
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        # Parse results
        results = []
        items = data.get("items", [])
        for item in items[:num_results]:
            result = _extract_model_info(item)
            results.append(result)
        
        return WebSearchResponse(
            results=results,
            query=query,
            success=True,
            error_message=None
        )
        
    except HTTPError as e:
        return WebSearchResponse(
            results=[],
            query=query,
            success=False,
            error_message=f"HTTP error: {e.code} - {e.reason}"
        )
    except URLError as e:
        return WebSearchResponse(
            results=[],
            query=query,
            success=False,
            error_message=f"URL error: {e.reason}"
        )
    except json.JSONDecodeError as e:
        return WebSearchResponse(
            results=[],
            query=query,
            success=False,
            error_message=f"Failed to parse response: {e}"
        )
    except Exception as e:
        return WebSearchResponse(
            results=[],
            query=query,
            success=False,
            error_message=f"Search failed: {str(e)}"
        )


def search_ml_models(
    task_type: str,
    data_modality: str,
    num_results: int = 4,
    api_key: Optional[str] = None,
    search_engine_id: Optional[str] = None
) -> WebSearchResponse:
    """Search for ML models suitable for a specific task.
    
    Constructs an optimized search query for finding ML models.
    
    Args:
        task_type: Type of ML task (e.g., "classification", "regression")
        data_modality: Data type (e.g., "tabular", "image", "text")
        num_results: Number of results to return
        api_key: Google API key (optional)
        search_engine_id: Google Custom Search Engine ID (optional)
        
    Returns:
        WebSearchResponse containing model search results
    """
    query = f"best {data_modality} {task_type} model kaggle python implementation"
    return web_search(
        query=query,
        num_results=num_results,
        api_key=api_key,
        search_engine_id=search_engine_id
    )
