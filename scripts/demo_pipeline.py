#!/usr/bin/env python
"""Demo script to test the MLE-STAR pipeline with mocked components.

This script demonstrates the pipeline flow without requiring actual LLM calls.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import TaskDescription, ModelCandidate
from mle_star.tools.web_search import search_ml_models_with_fallback, get_fallback_models
from mle_star.api.run_manager import RunManager, PipelineRun


def demo_web_search():
    """Demonstrate web search with fallback."""
    print("\n" + "="*60)
    print("DEMO: Web Search with Fallback")
    print("="*60)
    
    # Test fallback models for different task types
    test_cases = [
        ("classification", "tabular"),
        ("regression", "tabular"),
        ("classification", "text"),
        ("classification", "image"),
    ]
    
    for task_type, modality in test_cases:
        result = search_ml_models_with_fallback(
            task_type=task_type,
            data_modality=modality,
            num_results=2,
        )
        print(f"\n{modality.upper()} {task_type.upper()}:")
        for model in result.results:
            print(f"  - {model.model_name}: {model.snippet[:60]}...")
    
    print("\n✅ Web search fallback working correctly!")


def demo_run_manager():
    """Demonstrate run manager functionality."""
    print("\n" + "="*60)
    print("DEMO: Run Manager")
    print("="*60)
    
    manager = RunManager()
    
    # Create a task
    task = TaskDescription(
        description="Classify customer churn based on usage patterns",
        task_type="classification",
        data_modality="tabular",
        evaluation_metric="auc_roc",
        dataset_path="/data/churn.csv",
    )
    
    config = MLEStarConfig(
        num_retrieved_models=4,
        inner_loop_iterations=2,
        outer_loop_iterations=2,
    )
    
    # Create a run
    run = manager.create_run("demo_run_001", task, config)
    print(f"\n✅ Created run: {run.run_id}")
    print(f"   Status: {run.status}")
    print(f"   Phases initialized: {list(run.phases.keys())}")
    
    # Update agent status
    run.update_agent_status(1, "retriever", "running", "Searching for models...")
    print(f"\n✅ Updated retriever status to 'running'")
    
    run.update_agent_status(1, "retriever", "completed", "Found 4 models")
    print(f"✅ Updated retriever status to 'completed'")
    
    # Update phase status
    run.update_phase_status(1, "running", progress=25.0)
    print(f"\n✅ Phase 1 progress: {run.phases[1]['progress']}%")
    
    # Add log
    run.add_log("info", "Retriever", "Found XGBoost, LightGBM, CatBoost, RandomForest")
    print(f"✅ Added log entry (total logs: {len(run.logs)})")
    
    # List runs
    runs = manager.list_runs()
    print(f"\n✅ Total runs in manager: {len(runs)}")


def demo_config():
    """Demonstrate configuration."""
    print("\n" + "="*60)
    print("DEMO: Configuration")
    print("="*60)
    
    # Default config
    config = MLEStarConfig()
    print(f"\nDefault Configuration:")
    print(f"  num_retrieved_models: {config.num_retrieved_models}")
    print(f"  inner_loop_iterations: {config.inner_loop_iterations}")
    print(f"  outer_loop_iterations: {config.outer_loop_iterations}")
    print(f"  ensemble_iterations: {config.ensemble_iterations}")
    print(f"  model_id: {config.model_id}")
    
    # Serialize/deserialize
    config_dict = config.to_dict()
    restored = MLEStarConfig.from_dict(config_dict)
    print(f"\n✅ Config serialization/deserialization works!")
    assert restored.num_retrieved_models == config.num_retrieved_models


def demo_task_parsing():
    """Demonstrate task description parsing."""
    print("\n" + "="*60)
    print("DEMO: Task Description Parsing")
    print("="*60)
    
    # Parse from text
    text = """
    This is a binary classification task on tabular data.
    The goal is to predict customer churn using the dataset at '/data/train.csv'.
    The evaluation metric is AUC-ROC.
    """
    
    task = TaskDescription.parse_from_text(text)
    print(f"\nParsed Task:")
    print(f"  task_type: {task.task_type}")
    print(f"  data_modality: {task.data_modality}")
    print(f"  evaluation_metric: {task.evaluation_metric}")
    print(f"  dataset_path: {task.dataset_path}")
    
    print("\n✅ Task parsing works!")


def demo_fallback_models():
    """Demonstrate fallback model catalog."""
    print("\n" + "="*60)
    print("DEMO: Fallback Model Catalog")
    print("="*60)
    
    response = get_fallback_models("classification", "tabular", num_results=4)
    
    print(f"\nTabular Classification Models:")
    for i, model in enumerate(response.results, 1):
        print(f"\n{i}. {model.model_name}")
        print(f"   URL: {model.url}")
        print(f"   Description: {model.description[:80]}...")
        print(f"   Example code available: {'Yes' if model.example_code else 'No'}")
    
    print("\n✅ Fallback models include example code for immediate use!")


async def demo_api_models():
    """Demonstrate API models."""
    print("\n" + "="*60)
    print("DEMO: API Models")
    print("="*60)
    
    from mle_star.api.models import (
        PipelineStartRequest,
        TaskDescriptionRequest,
        MLEStarConfigRequest,
        PipelineStartResponse,
    )
    
    # Create a request
    request = PipelineStartRequest(
        task_description=TaskDescriptionRequest(
            description="Classify images of cats and dogs",
            task_type="classification",
            data_modality="image",
            evaluation_metric="accuracy",
            dataset_path="/data/images",
        ),
        config=MLEStarConfigRequest(
            num_retrieved_models=2,
            inner_loop_iterations=2,
        ),
    )
    
    print(f"\nPipeline Start Request:")
    print(f"  Task: {request.task_description.description[:50]}...")
    print(f"  Type: {request.task_description.task_type}")
    print(f"  Models to retrieve: {request.config.num_retrieved_models}")
    
    # Create a response
    response = PipelineStartResponse(
        run_id="test123",
        status="started",
        message="Pipeline started successfully",
    )
    
    print(f"\nPipeline Start Response:")
    print(f"  Run ID: {response.run_id}")
    print(f"  Status: {response.status}")
    
    print("\n✅ API models work correctly!")


def main():
    """Run all demos."""
    print("\n" + "#"*60)
    print("#" + " "*20 + "MLE-STAR DEMO" + " "*20 + "#")
    print("#"*60)
    
    demo_config()
    demo_task_parsing()
    demo_web_search()
    demo_fallback_models()
    demo_run_manager()
    asyncio.run(demo_api_models())
    
    print("\n" + "="*60)
    print("ALL DEMOS COMPLETED SUCCESSFULLY! ✅")
    print("="*60)
    print("\nThe MLE-STAR pipeline is ready for use.")
    print("To run with actual LLM calls, ensure you have:")
    print("  1. AWS credentials configured for Bedrock")
    print("  2. (Optional) Google API key for web search")
    print("\nStart the API server with:")
    print("  python -m uvicorn mle_star.api.server:app --port 8000")
    print()


if __name__ == "__main__":
    main()
