"""Run manager for tracking pipeline executions.

Manages the lifecycle of pipeline runs including:
- Creating new runs
- Tracking run status
- Storing run history
- Checkpoint management
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import threading

from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import TaskDescription


@dataclass
class PipelineRun:
    """Represents a single pipeline run."""
    run_id: str
    task: TaskDescription
    config: MLEStarConfig
    status: str = "pending"  # pending, running, paused, completed, error, stopped
    current_phase: Optional[int] = None
    is_running: bool = False
    is_paused: bool = False
    phases: dict[int, dict[str, Any]] = field(default_factory=dict)
    current_score: Optional[float] = None
    best_score: Optional[float] = None
    current_code: Optional[str] = None
    submission_path: Optional[str] = None
    error: Optional[str] = None
    logs: list[dict[str, Any]] = field(default_factory=list)
    checkpoint: Optional[dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize phase structures."""
        if not self.phases:
            self.phases = {
                1: {
                    "status": "pending",
                    "progress": 0.0,
                    "agents": [
                        {"id": "retriever", "name": "Retriever", "status": "idle"},
                        {"id": "evaluator", "name": "Evaluator", "status": "idle"},
                        {"id": "merger", "name": "Merger", "status": "idle"},
                        {"id": "leakage_checker", "name": "Leakage Checker", "status": "idle"},
                        {"id": "usage_checker", "name": "Usage Checker", "status": "idle"},
                    ],
                },
                2: {
                    "status": "pending",
                    "progress": 0.0,
                    "agents": [
                        {"id": "ablation", "name": "Ablation Study", "status": "idle"},
                        {"id": "summarizer", "name": "Summarizer", "status": "idle"},
                        {"id": "extractor", "name": "Extractor", "status": "idle"},
                        {"id": "coder", "name": "Coder", "status": "idle"},
                        {"id": "planner", "name": "Planner", "status": "idle"},
                        {"id": "debugger", "name": "Debugger", "status": "idle"},
                    ],
                },
                3: {
                    "status": "pending",
                    "progress": 0.0,
                    "agents": [
                        {"id": "ensemble_planner", "name": "Ensemble Planner", "status": "idle"},
                        {"id": "ensembler", "name": "Ensembler", "status": "idle"},
                        {"id": "submission", "name": "Submission", "status": "idle"},
                    ],
                },
            }
    
    def update_agent_status(
        self,
        phase: int,
        agent_id: str,
        status: str,
        message: Optional[str] = None,
    ) -> None:
        """Update the status of an agent."""
        if phase in self.phases:
            for agent in self.phases[phase]["agents"]:
                if agent["id"] == agent_id:
                    agent["status"] = status
                    agent["message"] = message
                    if status == "running":
                        agent["started_at"] = datetime.utcnow()
                    elif status in ("completed", "error"):
                        agent["completed_at"] = datetime.utcnow()
                    break
        self.updated_at = datetime.utcnow()
    
    def update_phase_status(
        self,
        phase: int,
        status: str,
        progress: Optional[float] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update the status of a phase."""
        if phase in self.phases:
            self.phases[phase]["status"] = status
            if progress is not None:
                self.phases[phase]["progress"] = progress
            if message:
                self.phases[phase]["message"] = message
            if status == "running":
                self.phases[phase]["started_at"] = datetime.utcnow()
            elif status in ("completed", "error"):
                self.phases[phase]["completed_at"] = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_log(
        self,
        level: str,
        agent: str,
        message: str,
    ) -> None:
        """Add a log entry."""
        self.logs.append({
            "timestamp": datetime.utcnow(),
            "level": level,
            "agent": agent,
            "message": message,
        })
    
    def save_checkpoint(self, checkpoint_data: dict[str, Any]) -> None:
        """Save a checkpoint for recovery."""
        self.checkpoint = checkpoint_data
        self.updated_at = datetime.utcnow()


class RunManager:
    """Manages pipeline runs with thread-safe access."""
    
    def __init__(self):
        """Initialize the run manager."""
        self._runs: dict[str, PipelineRun] = {}
        self._lock = threading.Lock()
    
    def create_run(
        self,
        run_id: str,
        task: TaskDescription,
        config: MLEStarConfig,
    ) -> PipelineRun:
        """Create and register a new pipeline run."""
        with self._lock:
            run = PipelineRun(
                run_id=run_id,
                task=task,
                config=config,
            )
            self._runs[run_id] = run
            return run
    
    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """Get a pipeline run by ID."""
        with self._lock:
            return self._runs.get(run_id)
    
    def update_run(self, run_id: str, **kwargs) -> Optional[PipelineRun]:
        """Update a pipeline run."""
        with self._lock:
            run = self._runs.get(run_id)
            if run:
                for key, value in kwargs.items():
                    if hasattr(run, key):
                        setattr(run, key, value)
                run.updated_at = datetime.utcnow()
            return run
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a pipeline run."""
        with self._lock:
            if run_id in self._runs:
                del self._runs[run_id]
                return True
            return False
    
    def list_runs(
        self,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> list[PipelineRun]:
        """List pipeline runs with optional filtering."""
        with self._lock:
            runs = list(self._runs.values())
            
            # Filter by status if specified
            if status:
                runs = [r for r in runs if r.status == status]
            
            # Sort by created_at descending
            runs.sort(key=lambda r: r.created_at, reverse=True)
            
            # Apply pagination
            return runs[offset:offset + limit]
    
    def total_runs(self, status: Optional[str] = None) -> int:
        """Get total number of runs."""
        with self._lock:
            if status:
                return sum(1 for r in self._runs.values() if r.status == status)
            return len(self._runs)
    
    def cleanup_old_runs(self, max_age_hours: int = 24) -> int:
        """Remove runs older than max_age_hours."""
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed = 0
        
        with self._lock:
            to_remove = [
                run_id for run_id, run in self._runs.items()
                if run.created_at < cutoff and run.status in ("completed", "error", "stopped")
            ]
            for run_id in to_remove:
                del self._runs[run_id]
                removed += 1
        
        return removed
