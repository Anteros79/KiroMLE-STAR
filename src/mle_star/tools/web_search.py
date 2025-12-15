"""Web search tool for model retrieval in MLE-STAR agents.

Supports Google Custom Search API with fallback to curated model recommendations.
Includes caching to reduce API calls for identical queries.
"""

import os
import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from pathlib import Path

# Simple in-memory cache for search results
_search_cache: dict[str, tuple[float, "WebSearchResponse"]] = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour cache


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


# Curated fallback models by task type and modality
FALLBACK_MODELS: dict[str, dict[str, list[SearchResult]]] = {
    "tabular": {
        "classification": [
            SearchResult(
                title="XGBoost Classifier",
                url="https://xgboost.readthedocs.io/",
                snippet="Gradient boosting framework optimized for speed and performance. Top choice for tabular classification.",
                model_name="XGBoost",
                description="Extreme Gradient Boosting for classification tasks",
                example_code="""import xgboost as xgb
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
model = xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1)
model.fit(X_train, y_train)
predictions = model.predict(X_val)"""
            ),
            SearchResult(
                title="LightGBM Classifier",
                url="https://lightgbm.readthedocs.io/",
                snippet="Fast gradient boosting framework using tree-based learning. Excellent for large datasets.",
                model_name="LightGBM",
                description="Light Gradient Boosting Machine for classification",
                example_code="""import lightgbm as lgb
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
model = lgb.LGBMClassifier(n_estimators=100, num_leaves=31)
model.fit(X_train, y_train)
predictions = model.predict(X_val)"""
            ),
            SearchResult(
                title="CatBoost Classifier",
                url="https://catboost.ai/",
                snippet="Gradient boosting with native categorical feature support. Handles missing values automatically.",
                model_name="CatBoost",
                description="Categorical Boosting for classification with automatic category handling",
                example_code="""from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
model = CatBoostClassifier(iterations=100, depth=6, verbose=False)
model.fit(X_train, y_train)
predictions = model.predict(X_val)"""
            ),
            SearchResult(
                title="Random Forest Classifier",
                url="https://scikit-learn.org/stable/modules/ensemble.html",
                snippet="Ensemble of decision trees with bagging. Robust baseline for classification tasks.",
                model_name="RandomForest",
                description="Random Forest ensemble classifier from scikit-learn",
                example_code="""from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
model = RandomForestClassifier(n_estimators=100, max_depth=10)
model.fit(X_train, y_train)
predictions = model.predict(X_val)"""
            ),
        ],
        "regression": [
            SearchResult(
                title="XGBoost Regressor",
                url="https://xgboost.readthedocs.io/",
                snippet="Gradient boosting for regression tasks. State-of-the-art for tabular regression.",
                model_name="XGBoost",
                description="Extreme Gradient Boosting for regression",
                example_code="""import xgboost as xgb
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
model = xgb.XGBRegressor(n_estimators=100, max_depth=6, learning_rate=0.1)
model.fit(X_train, y_train)
predictions = model.predict(X_val)"""
            ),
            SearchResult(
                title="LightGBM Regressor",
                url="https://lightgbm.readthedocs.io/",
                snippet="Fast gradient boosting for regression. Efficient with large datasets.",
                model_name="LightGBM",
                description="Light Gradient Boosting Machine for regression",
                example_code="""import lightgbm as lgb
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
model = lgb.LGBMRegressor(n_estimators=100, num_leaves=31)
model.fit(X_train, y_train)
predictions = model.predict(X_val)"""
            ),
            SearchResult(
                title="CatBoost Regressor",
                url="https://catboost.ai/",
                snippet="Gradient boosting regressor with categorical feature support.",
                model_name="CatBoost",
                description="Categorical Boosting for regression",
                example_code="""from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
model = CatBoostRegressor(iterations=100, depth=6, verbose=False)
model.fit(X_train, y_train)
predictions = model.predict(X_val)"""
            ),
            SearchResult(
                title="Random Forest Regressor",
                url="https://scikit-learn.org/stable/modules/ensemble.html",
                snippet="Ensemble of decision trees for regression. Robust baseline.",
                model_name="RandomForest",
                description="Random Forest ensemble regressor",
                example_code="""from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
model = RandomForestRegressor(n_estimators=100, max_depth=10)
model.fit(X_train, y_train)
predictions = model.predict(X_val)"""
            ),
        ],
    },
    "text": {
        "classification": [
            SearchResult(
                title="DistilBERT for Text Classification",
                url="https://huggingface.co/distilbert-base-uncased",
                snippet="Lightweight BERT model for text classification. Fast inference with good accuracy.",
                model_name="DistilBERT",
                description="Distilled BERT for efficient text classification",
                example_code="""from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch

tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=2)
inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
outputs = model(**inputs)"""
            ),
            SearchResult(
                title="TF-IDF + Logistic Regression",
                url="https://scikit-learn.org/stable/modules/feature_extraction.html",
                snippet="Classic text classification pipeline. Fast and interpretable baseline.",
                model_name="TF-IDF+LogReg",
                description="TF-IDF vectorization with Logistic Regression",
                example_code="""from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=10000)),
    ('clf', LogisticRegression(max_iter=1000))
])
pipeline.fit(X_train, y_train)
predictions = pipeline.predict(X_val)"""
            ),
        ],
    },
    "image": {
        "classification": [
            SearchResult(
                title="EfficientNet",
                url="https://pytorch.org/vision/stable/models.html",
                snippet="State-of-the-art image classification with efficient scaling. Top Kaggle choice.",
                model_name="EfficientNet",
                description="EfficientNet for image classification",
                example_code="""import torch
import torchvision.models as models

model = models.efficientnet_b0(pretrained=True)
model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)
model.train()"""
            ),
            SearchResult(
                title="ResNet",
                url="https://pytorch.org/vision/stable/models.html",
                snippet="Deep residual network for image classification. Reliable baseline.",
                model_name="ResNet",
                description="Residual Network for image classification",
                example_code="""import torch
import torchvision.models as models

model = models.resnet50(pretrained=True)
model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
model.train()"""
            ),
        ],
    },
    "audio": {
        "classification": [
            SearchResult(
                title="Wav2Vec2 for Audio Classification",
                url="https://huggingface.co/facebook/wav2vec2-base",
                snippet="Self-supervised audio model. Excellent for speech and audio classification.",
                model_name="Wav2Vec2",
                description="Wav2Vec2 for audio classification",
                example_code="""from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor

processor = Wav2Vec2Processor.from_pretrained('facebook/wav2vec2-base')
model = Wav2Vec2ForSequenceClassification.from_pretrained('facebook/wav2vec2-base', num_labels=num_classes)"""
            ),
        ],
    },
}


def get_fallback_models(
    task_type: str,
    data_modality: str,
    num_results: int = 4
) -> WebSearchResponse:
    """Get curated fallback models when search API is unavailable.
    
    Args:
        task_type: Type of ML task
        data_modality: Data modality
        num_results: Number of results to return
        
    Returns:
        WebSearchResponse with fallback models
    """
    # Normalize inputs
    modality = data_modality.lower()
    task = task_type.lower()
    
    # Map task types to base types
    if "classif" in task:
        task = "classification"
    elif "regress" in task:
        task = "regression"
    
    # Get fallback models
    modality_models = FALLBACK_MODELS.get(modality, FALLBACK_MODELS.get("tabular", {}))
    task_models = modality_models.get(task, modality_models.get("classification", []))
    
    if not task_models:
        # Ultimate fallback: tabular classification
        task_models = FALLBACK_MODELS["tabular"]["classification"]
    
    return WebSearchResponse(
        results=task_models[:num_results],
        query=f"fallback:{modality}:{task}",
        success=True,
        error_message=None
    )


def _get_cache_key(query: str, num_results: int) -> str:
    """Generate cache key for a search query."""
    return hashlib.md5(f"{query}:{num_results}".encode()).hexdigest()


def web_search_with_cache(
    query: str,
    num_results: int = 4,
    api_key: Optional[str] = None,
    search_engine_id: Optional[str] = None,
    use_cache: bool = True
) -> WebSearchResponse:
    """Web search with caching support.
    
    Args:
        query: Search query
        num_results: Number of results
        api_key: Google API key
        search_engine_id: Search engine ID
        use_cache: Whether to use cache
        
    Returns:
        WebSearchResponse with results
    """
    cache_key = _get_cache_key(query, num_results)
    
    # Check cache
    if use_cache and cache_key in _search_cache:
        cached_time, cached_response = _search_cache[cache_key]
        if time.time() - cached_time < _CACHE_TTL_SECONDS:
            return cached_response
    
    # Perform search
    response = web_search(query, num_results, api_key, search_engine_id)
    
    # Cache successful results
    if response.success and use_cache:
        _search_cache[cache_key] = (time.time(), response)
    
    return response


def search_ml_models_with_fallback(
    task_type: str,
    data_modality: str,
    num_results: int = 4,
    api_key: Optional[str] = None,
    search_engine_id: Optional[str] = None
) -> WebSearchResponse:
    """Search for ML models with fallback to curated recommendations.
    
    First attempts Google Custom Search. If that fails, returns curated
    fallback models appropriate for the task type and data modality.
    
    Args:
        task_type: Type of ML task
        data_modality: Data modality
        num_results: Number of results
        api_key: Google API key
        search_engine_id: Search engine ID
        
    Returns:
        WebSearchResponse with model recommendations
    """
    # Try web search first
    response = search_ml_models(
        task_type=task_type,
        data_modality=data_modality,
        num_results=num_results,
        api_key=api_key,
        search_engine_id=search_engine_id
    )
    
    # If search succeeded, return results
    if response.success and response.results:
        return response
    
    # Fall back to curated models
    fallback = get_fallback_models(task_type, data_modality, num_results)
    fallback.error_message = f"Search failed ({response.error_message}), using fallback models"
    return fallback


def clear_search_cache() -> None:
    """Clear the search results cache."""
    global _search_cache
    _search_cache = {}
