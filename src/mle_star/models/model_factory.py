"""Model factory for creating LLM instances based on configuration."""

from typing import Any
from mle_star.models.config import MLEStarConfig


def create_model(config: MLEStarConfig) -> Any:
    """Create an LLM model instance based on configuration.
    
    Supports:
    - Lemonade (llama.cpp compatible server with GGUF models)
    - Ollama (local models like Gemma 3 27B)
    - AWS Bedrock (Claude, etc.)
    - OpenAI
    
    Args:
        config: MLE-STAR configuration with model settings
        
    Returns:
        Model instance compatible with Strands Agent
    """
    if config.model_provider == "lemonade":
        # Lemonade uses llama.cpp server with OpenAI-compatible API
        try:
            from strands.models.openai import OpenAIModel
            return OpenAIModel(
                model_id=config.model_id,
                client_args={
                    "base_url": f"{config.lemonade_base_url}/v1",
                    "api_key": "not-needed",  # llama.cpp doesn't require API key
                },
            )
        except ImportError:
            # Fallback: try using litellm or direct OpenAI client
            try:
                import openai
                client = openai.OpenAI(
                    base_url=f"{config.lemonade_base_url}/v1",
                    api_key="not-needed",
                )
                return client
            except ImportError:
                raise ImportError(
                    "Neither strands.models.openai nor openai package available. "
                    "Install with: pip install openai"
                )
    
    elif config.model_provider == "ollama":
        try:
            from strands.models.ollama import OllamaModel
            return OllamaModel(
                model_id=config.model_id,
                host=config.ollama_base_url,
            )
        except ImportError:
            # Fallback: return model_id string and let Strands handle it
            # with OLLAMA_HOST environment variable
            import os
            os.environ.setdefault("OLLAMA_HOST", config.ollama_base_url)
            return f"ollama/{config.model_id}"
    
    elif config.model_provider == "bedrock":
        try:
            from strands.models.bedrock import BedrockModel
            return BedrockModel(model_id=config.model_id)
        except ImportError:
            return config.model_id
    
    elif config.model_provider == "openai":
        try:
            from strands.models.openai import OpenAIModel
            return OpenAIModel(model_id=config.model_id)
        except ImportError:
            return config.model_id
    
    # Default: return model_id string
    return config.model_id


def get_model_display_name(config: MLEStarConfig) -> str:
    """Get a human-readable display name for the configured model.
    
    Args:
        config: MLE-STAR configuration
        
    Returns:
        Human-readable model name
    """
    provider_names = {
        "lemonade": "Lemonade (llama.cpp)",
        "ollama": "Ollama",
        "bedrock": "AWS Bedrock",
        "openai": "OpenAI",
    }
    provider = provider_names.get(config.model_provider, config.model_provider)
    return f"{config.model_id} ({provider})"
