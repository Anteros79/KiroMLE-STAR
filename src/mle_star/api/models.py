"""Pydantic models for MLE-STAR API requests and responses."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class PhaseStatus(str, Enum):
    """Status of a pipeline phase."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class AgentStatus(str, Enum):
    """Status of an individual agent."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


# Request Models

class MLEStarConfigRequest(BaseModel):
    """Configuration for MLE-STAR pipeline."""
    num_retrieved_models: int = Field(default=4, ge=1, le=10)
    inner_loop_iterations: int = Field(default=4, ge=1, le=10)
    outer_loop_iterations: int = Field(default=4, ge=1, le=10)
    ensemble_iterations: int = Field(default=5, ge=1, le=10)
    max_debug_retries: int = Field(default=3, ge=1, le=10)
    model_id: str = Field(default="qwen3-next-72b")
    model_provider: str = Field(default="lemonade")
    ollama_base_url: str = Field(default="http://localhost:11434")
    lemonade_base_url: str = Field(default="http://localhost:8080")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=256, le=32768)


class TaskDescriptionRequest(BaseModel):
    """Task description for the ML problem."""
    description: str = Field(..., min_length=10)
    task_type: str = Field(default="classification")
    data_modality: str = Field(default="tabular")
    evaluation_metric: str = Field(default="accuracy")
    dataset_path: str = Field(...)
    submission_format: Optional[str] = None


class PipelineStartRequest(BaseModel):
    """Request to start a new pipeline run."""
    task_description: TaskDescriptionRequest
    config: Optional[MLEStarConfigRequest] = None
    dataset_path: Optional[str] = None  # Override from task_description


class PipelinePauseRequest(BaseModel):
    """Request to pause a pipeline run."""
    run_id: str


class PipelineResumeRequest(BaseModel):
    """Request to resume a paused pipeline run."""
    run_id: str


# Response Models

class AgentStatusUpdate(BaseModel):
    """Status update for a single agent."""
    agent_id: str
    agent_name: str
    status: AgentStatus
    phase: int
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict[str, Any]] = None


class PhaseStatusUpdate(BaseModel):
    """Status update for a pipeline phase."""
    phase: int
    status: PhaseStatus
    progress: float = Field(ge=0.0, le=100.0)
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agents: list[AgentStatusUpdate] = Field(default_factory=list)


class PipelineStartResponse(BaseModel):
    """Response after starting a pipeline."""
    run_id: str
    status: str = "started"
    message: str = "Pipeline started successfully"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineStatusResponse(BaseModel):
    """Full status response for a pipeline run."""
    run_id: str
    status: str  # "running", "paused", "completed", "error"
    current_phase: Optional[int] = None
    is_running: bool = False
    is_paused: bool = False
    phases: list[PhaseStatusUpdate] = Field(default_factory=list)
    current_score: Optional[float] = None
    best_score: Optional[float] = None
    current_code: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SubmissionResponse(BaseModel):
    """Response for submission download."""
    run_id: str
    submission_path: str
    file_size: int
    rows: int
    columns: list[str]
    preview: list[list[str]]  # First N rows


class LogEntry(BaseModel):
    """A single log entry."""
    timestamp: datetime
    level: str  # "info", "warning", "error", "success"
    agent: str
    message: str


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "agent_update", "phase_update", "log", "score_update", "error"
    run_id: str
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
