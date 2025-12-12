"""MLE-STAR: Machine Learning Engineering Agent via Search and Targeted Refinement."""

__version__ = "0.1.0"

# Export core components
from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import (
    TaskDescription,
    ModelCandidate,
    SolutionState,
    RefinementAttempt,
    EnsembleResult,
)

# Export graph orchestrators
from mle_star.graphs import (
    InitialSolutionGraph,
    create_initial_solution_graph,
    InitialSolutionState,
    RefinementLoopNode,
    RefinementGraph,
    create_refinement_graph,
    RefinementState,
    EnsembleGraph,
    create_ensemble_graph,
    EnsembleState,
)

# Export main orchestrator
from mle_star.orchestrator import (
    MLEStarOrchestrator,
    OrchestratorState,
    create_orchestrator,
)

__all__ = [
    # Version
    "__version__",
    # Configuration
    "MLEStarConfig",
    # Data Models
    "TaskDescription",
    "ModelCandidate",
    "SolutionState",
    "RefinementAttempt",
    "EnsembleResult",
    # Graph Orchestrators
    "InitialSolutionGraph",
    "create_initial_solution_graph",
    "InitialSolutionState",
    "RefinementLoopNode",
    "RefinementGraph",
    "create_refinement_graph",
    "RefinementState",
    "EnsembleGraph",
    "create_ensemble_graph",
    "EnsembleState",
    # Main Orchestrator
    "MLEStarOrchestrator",
    "OrchestratorState",
    "create_orchestrator",
]
