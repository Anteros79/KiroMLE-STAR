"""Unit tests for web search tool with fallback functionality."""

import pytest
from mle_star.tools.web_search import (
    SearchResult,
    WebSearchResponse,
    web_search,
    search_ml_models,
    search_ml_models_with_fallback,
    get_fallback_models,
    web_search_with_cache,
    clear_search_cache,
    FALLBACK_MODELS,
    _get_cache_key,
)


class TestSearchResult:
    """Tests for SearchResult dataclass."""
    
    def test_search_result_creation(self):
        """Test SearchResult can be created with required fields."""
        result = SearchResult(
            title="XGBoost",
            url="https://xgboost.readthedocs.io/",
            snippet="Gradient boosting framework",
        )
        
        assert result.title == "XGBoost"
        assert result.url == "https://xgboost.readthedocs.io/"
        assert result.snippet == "Gradient boosting framework"
        assert result.model_name is None
        assert result.example_code is None
    
    def test_search_result_with_optional_fields(self):
        """Test SearchResult with all optional fields."""
        result = SearchResult(
            title="XGBoost",
            url="https://xgboost.readthedocs.io/",
            snippet="Gradient boosting framework",
            model_name="XGBoost",
            description="Extreme Gradient Boosting",
            example_code="import xgboost as xgb",
        )
        
        assert result.model_name == "XGBoost"
        assert result.description == "Extreme Gradient Boosting"
        assert result.example_code == "import xgboost as xgb"


class TestWebSearchResponse:
    """Tests for WebSearchResponse dataclass."""
    
    def test_empty_response(self):
        """Test empty WebSearchResponse."""
        response = WebSearchResponse()
        
        assert response.results == []
        assert response.query == ""
        assert response.success is False
        assert response.error_message is None
    
    def test_successful_response(self):
        """Test successful WebSearchResponse."""
        results = [
            SearchResult(title="Model 1", url="http://example.com", snippet="Test"),
        ]
        response = WebSearchResponse(
            results=results,
            query="test query",
            success=True,
        )
        
        assert len(response.results) == 1
        assert response.query == "test query"
        assert response.success is True


class TestFallbackModels:
    """Tests for fallback model functionality."""
    
    def test_fallback_models_exist(self):
        """Test that fallback models are defined."""
        assert "tabular" in FALLBACK_MODELS
        assert "text" in FALLBACK_MODELS
        assert "image" in FALLBACK_MODELS
        assert "audio" in FALLBACK_MODELS
    
    def test_tabular_classification_fallbacks(self):
        """Test tabular classification fallback models."""
        models = FALLBACK_MODELS["tabular"]["classification"]
        
        assert len(models) >= 4
        model_names = [m.model_name for m in models]
        assert "XGBoost" in model_names
        assert "LightGBM" in model_names
        assert "CatBoost" in model_names
        assert "RandomForest" in model_names
    
    def test_tabular_regression_fallbacks(self):
        """Test tabular regression fallback models."""
        models = FALLBACK_MODELS["tabular"]["regression"]
        
        assert len(models) >= 4
        model_names = [m.model_name for m in models]
        assert "XGBoost" in model_names
    
    def test_fallback_models_have_example_code(self):
        """Test that fallback models include example code."""
        for modality, tasks in FALLBACK_MODELS.items():
            for task_type, models in tasks.items():
                for model in models:
                    assert model.example_code is not None, \
                        f"Missing example code for {modality}/{task_type}/{model.model_name}"
                    assert len(model.example_code) > 10, \
                        f"Example code too short for {model.model_name}"


class TestGetFallbackModels:
    """Tests for get_fallback_models function."""
    
    def test_get_tabular_classification(self):
        """Test getting tabular classification fallbacks."""
        response = get_fallback_models("classification", "tabular", num_results=4)
        
        assert response.success is True
        assert len(response.results) == 4
        assert "fallback" in response.query
    
    def test_get_tabular_regression(self):
        """Test getting tabular regression fallbacks."""
        response = get_fallback_models("regression", "tabular", num_results=4)
        
        assert response.success is True
        assert len(response.results) == 4
    
    def test_get_text_classification(self):
        """Test getting text classification fallbacks."""
        response = get_fallback_models("classification", "text", num_results=2)
        
        assert response.success is True
        assert len(response.results) == 2
    
    def test_get_image_classification(self):
        """Test getting image classification fallbacks."""
        response = get_fallback_models("classification", "image", num_results=2)
        
        assert response.success is True
        assert len(response.results) == 2
    
    def test_unknown_modality_falls_back_to_tabular(self):
        """Test unknown modality falls back to tabular."""
        response = get_fallback_models("classification", "unknown_modality", num_results=4)
        
        assert response.success is True
        assert len(response.results) == 4
    
    def test_task_type_normalization(self):
        """Test task type normalization (e.g., 'binary_classification' -> 'classification')."""
        response = get_fallback_models("binary_classification", "tabular", num_results=4)
        
        assert response.success is True
        assert len(response.results) == 4
    
    def test_num_results_limiting(self):
        """Test that num_results limits the output."""
        response = get_fallback_models("classification", "tabular", num_results=2)
        
        assert len(response.results) == 2


class TestSearchWithFallback:
    """Tests for search_ml_models_with_fallback function."""
    
    def test_fallback_when_no_api_key(self):
        """Test fallback is used when API key is missing."""
        # Clear any environment variables
        import os
        original_key = os.environ.pop("GOOGLE_API_KEY", None)
        original_cx = os.environ.pop("GOOGLE_SEARCH_ENGINE_ID", None)
        
        try:
            response = search_ml_models_with_fallback(
                task_type="classification",
                data_modality="tabular",
                num_results=4,
            )
            
            assert response.success is True
            assert len(response.results) == 4
            assert "fallback" in response.error_message.lower() or "fallback" in response.query
        finally:
            # Restore environment variables
            if original_key:
                os.environ["GOOGLE_API_KEY"] = original_key
            if original_cx:
                os.environ["GOOGLE_SEARCH_ENGINE_ID"] = original_cx


class TestSearchCache:
    """Tests for search caching functionality."""
    
    def setup_method(self):
        """Clear cache before each test."""
        clear_search_cache()
    
    def test_cache_key_generation(self):
        """Test cache key is generated consistently."""
        key1 = _get_cache_key("test query", 4)
        key2 = _get_cache_key("test query", 4)
        key3 = _get_cache_key("different query", 4)
        key4 = _get_cache_key("test query", 5)
        
        assert key1 == key2
        assert key1 != key3
        assert key1 != key4
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # This should not raise any errors
        clear_search_cache()


class TestWebSearchWithoutCredentials:
    """Tests for web_search when credentials are missing."""
    
    def test_returns_error_without_credentials(self):
        """Test web_search returns error when credentials are missing."""
        import os
        original_key = os.environ.pop("GOOGLE_API_KEY", None)
        original_cx = os.environ.pop("GOOGLE_SEARCH_ENGINE_ID", None)
        
        try:
            response = web_search("test query", num_results=4)
            
            assert response.success is False
            assert "credentials" in response.error_message.lower() or "api" in response.error_message.lower()
        finally:
            if original_key:
                os.environ["GOOGLE_API_KEY"] = original_key
            if original_cx:
                os.environ["GOOGLE_SEARCH_ENGINE_ID"] = original_cx
