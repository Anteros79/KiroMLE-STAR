"""Configuration dataclass for MLE-STAR agent."""

from dataclasses import dataclass, field, asdict
from typing import Any, Literal


@dataclass
class MLEStarConfig:
    """Configuration for MLE-STAR agent.
    
    Attributes:
        num_retrieved_models: Number of model candidates to retrieve from web search (default: 4)
        inner_loop_iterations: Number of refinement iterations per code block (default: 4)
        outer_loop_iterations: Number of outer loop iterations for targeting different blocks (default: 4)
        ensemble_iterations: Number of ensemble strategy exploration rounds (default: 5)
        max_debug_retries: Maximum number of debugging attempts before giving up (default: 3)
        model_id: The LLM model identifier to use for agents
        model_provider: The model provider (ollama, bedrock, openai, lemonade)
        ollama_base_url: Base URL for Ollama API (default: http://localhost:11434)
        lemonade_base_url: Base URL for Lemonade/llama.cpp server (default: http://localhost:8080)
        temperature: Temperature parameter for LLM generation
        max_tokens: Maximum tokens for LLM responses
    """
    
    # Core iteration parameters
    num_retrieved_models: int = 4
    inner_loop_iterations: int = 4
    outer_loop_iterations: int = 4
    ensemble_iterations: int = 5
    max_debug_retries: int = 3
    
    # LLM parameters
    model_id: str = "qwen3-next-72b"
    model_provider: Literal["ollama", "bedrock", "openai", "lemonade"] = "lemonade"
    ollama_base_url: str = "http://localhost:11434"
    lemonade_base_url: str = "http://localhost:8080"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration.
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MLEStarConfig":
        """Deserialize configuration from dictionary.
        
        Args:
            data: Dictionary containing configuration parameters.
            
        Returns:
            MLEStarConfig instance with values from the dictionary.
        """
        return cls(
            num_retrieved_models=data.get("num_retrieved_models", 4),
            inner_loop_iterations=data.get("inner_loop_iterations", 4),
            outer_loop_iterations=data.get("outer_loop_iterations", 4),
            ensemble_iterations=data.get("ensemble_iterations", 5),
            max_debug_retries=data.get("max_debug_retries", 3),
            model_id=data.get("model_id", "qwen3-next-72b"),
            model_provider=data.get("model_provider", "lemonade"),
            ollama_base_url=data.get("ollama_base_url", "http://localhost:11434"),
            lemonade_base_url=data.get("lemonade_base_url", "http://localhost:8080"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
        )
