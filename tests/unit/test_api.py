"""Unit tests for MLE-STAR API server."""

import pytest
from datetime import datetime

from mle_star.api.models import (
    MLEStarConfigRequest,
    TaskDescriptionRequest,
    PipelineStartRequest,
    PipelineStartResponse,
    PipelineStatusResponse,
    PhaseStatusUpdate,
    AgentStatusUpdate,
    PhaseStatus,
    AgentStatus,
    WebSocketMessage,
    LogEntry,
)
from mle_star.api.run_manager import RunManager, PipelineRun
from mle_star.models.config import MLEStarConfig
from mle_star.models.data_models import TaskDescription


class TestAPIModels:
    """Tests for API Pydantic models."""
    
    def test_config_request_defaults(self):
        """Test MLEStarConfigRequest has correct defaults."""
        config = MLEStarConfigRequest()
        
        assert config.num_retrieved_models == 4
        assert config.inner_loop_iterations == 4
        assert config.outer_loop_iterations == 4
        assert config.ensemble_iterations == 5
        assert config.max_debug_retries == 3
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
    
    def test_config_request_validation(self):
        """Test MLEStarConfigRequest validates bounds."""
        # Valid config
        config = MLEStarConfigRequest(
            num_retrieved_models=5,
            temperature=1.0,
        )
        assert config.num_retrieved_models == 5
        
        # Invalid config should raise
        with pytest.raises(ValueError):
            MLEStarConfigRequest(num_retrieved_models=0)  # Below min
        
        with pytest.raises(ValueError):
            MLEStarConfigRequest(temperature=3.0)  # Above max
    
    def test_task_description_request(self):
        """Test TaskDescriptionRequest creation."""
        task = TaskDescriptionRequest(
            description="Classify images of cats and dogs",
            task_type="classification",
            data_modality="image",
            evaluation_metric="accuracy",
            dataset_path="/data/images",
        )
        
        assert task.description == "Classify images of cats and dogs"
        assert task.task_type == "classification"
        assert task.submission_format is None
    
    def test_task_description_validation(self):
        """Test TaskDescriptionRequest validates required fields."""
        with pytest.raises(ValueError):
            TaskDescriptionRequest(
                description="Short",  # Too short (min 10 chars)
                task_type="classification",
                data_modality="tabular",
                evaluation_metric="accuracy",
                dataset_path="/data",
            )
    
    def test_pipeline_start_request(self):
        """Test PipelineStartRequest creation."""
        request = PipelineStartRequest(
            task_description=TaskDescriptionRequest(
                description="Test classification task",
                task_type="classification",
                data_modality="tabular",
                evaluation_metric="accuracy",
                dataset_path="/data/train.csv",
            ),
            config=MLEStarConfigRequest(num_retrieved_models=2),
        )
        
        assert request.task_description.task_type == "classification"
        assert request.config.num_retrieved_models == 2
    
    def test_pipeline_start_response(self):
        """Test PipelineStartResponse creation."""
        response = PipelineStartResponse(
            run_id="abc123",
            status="started",
            message="Pipeline started successfully",
        )
        
        assert response.run_id == "abc123"
        assert response.status == "started"
        assert response.created_at is not None
    
    def test_agent_status_update(self):
        """Test AgentStatusUpdate creation."""
        update = AgentStatusUpdate(
            agent_id="retriever",
            agent_name="Retriever",
            status=AgentStatus.RUNNING,
            phase=1,
            message="Searching for models...",
        )
        
        assert update.agent_id == "retriever"
        assert update.status == AgentStatus.RUNNING
        assert update.phase == 1
    
    def test_phase_status_update(self):
        """Test PhaseStatusUpdate creation."""
        update = PhaseStatusUpdate(
            phase=1,
            status=PhaseStatus.RUNNING,
            progress=50.0,
            message="Processing...",
            agents=[
                AgentStatusUpdate(
                    agent_id="retriever",
                    agent_name="Retriever",
                    status=AgentStatus.COMPLETED,
                    phase=1,
                ),
            ],
        )
        
        assert update.phase == 1
        assert update.progress == 50.0
        assert len(update.agents) == 1
    
    def test_websocket_message(self):
        """Test WebSocketMessage creation."""
        message = WebSocketMessage(
            type="agent_update",
            run_id="abc123",
            data={"agent_id": "retriever", "status": "completed"},
        )
        
        assert message.type == "agent_update"
        assert message.run_id == "abc123"
        assert message.timestamp is not None
    
    def test_log_entry(self):
        """Test LogEntry creation."""
        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level="info",
            agent="Retriever",
            message="Found 4 model candidates",
        )
        
        assert entry.level == "info"
        assert entry.agent == "Retriever"


class TestRunManager:
    """Tests for RunManager class."""
    
    def setup_method(self):
        """Create a fresh RunManager for each test."""
        self.manager = RunManager()
        self.task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        self.config = MLEStarConfig()
    
    def test_create_run(self):
        """Test creating a new run."""
        run = self.manager.create_run("run1", self.task, self.config)
        
        assert run.run_id == "run1"
        assert run.task == self.task
        assert run.config == self.config
        assert run.status == "pending"
        assert run.is_running is False
    
    def test_get_run(self):
        """Test getting a run by ID."""
        self.manager.create_run("run1", self.task, self.config)
        
        run = self.manager.get_run("run1")
        assert run is not None
        assert run.run_id == "run1"
        
        # Non-existent run
        assert self.manager.get_run("nonexistent") is None
    
    def test_update_run(self):
        """Test updating a run."""
        self.manager.create_run("run1", self.task, self.config)
        
        run = self.manager.update_run("run1", status="running", is_running=True)
        
        assert run.status == "running"
        assert run.is_running is True
    
    def test_delete_run(self):
        """Test deleting a run."""
        self.manager.create_run("run1", self.task, self.config)
        
        assert self.manager.delete_run("run1") is True
        assert self.manager.get_run("run1") is None
        assert self.manager.delete_run("run1") is False  # Already deleted
    
    def test_list_runs(self):
        """Test listing runs."""
        self.manager.create_run("run1", self.task, self.config)
        self.manager.create_run("run2", self.task, self.config)
        self.manager.create_run("run3", self.task, self.config)
        
        runs = self.manager.list_runs(limit=2)
        assert len(runs) == 2
        
        all_runs = self.manager.list_runs(limit=10)
        assert len(all_runs) == 3
    
    def test_total_runs(self):
        """Test counting total runs."""
        assert self.manager.total_runs() == 0
        
        self.manager.create_run("run1", self.task, self.config)
        assert self.manager.total_runs() == 1
        
        self.manager.create_run("run2", self.task, self.config)
        assert self.manager.total_runs() == 2


class TestPipelineRun:
    """Tests for PipelineRun dataclass."""
    
    def setup_method(self):
        """Create a fresh PipelineRun for each test."""
        self.task = TaskDescription(
            description="Test task",
            task_type="classification",
            data_modality="tabular",
            evaluation_metric="accuracy",
            dataset_path="/data/test.csv",
        )
        self.config = MLEStarConfig()
        self.run = PipelineRun(
            run_id="test_run",
            task=self.task,
            config=self.config,
        )
    
    def test_initial_phases(self):
        """Test that phases are initialized correctly."""
        assert 1 in self.run.phases
        assert 2 in self.run.phases
        assert 3 in self.run.phases
        
        # Check phase 1 agents
        phase1_agents = self.run.phases[1]["agents"]
        agent_ids = [a["id"] for a in phase1_agents]
        assert "retriever" in agent_ids
        assert "evaluator" in agent_ids
        assert "merger" in agent_ids
    
    def test_update_agent_status(self):
        """Test updating agent status."""
        self.run.update_agent_status(1, "retriever", "running", "Searching...")
        
        agent = next(a for a in self.run.phases[1]["agents"] if a["id"] == "retriever")
        assert agent["status"] == "running"
        assert agent["message"] == "Searching..."
        assert "started_at" in agent
    
    def test_update_phase_status(self):
        """Test updating phase status."""
        self.run.update_phase_status(1, "running", progress=25.0, message="Processing")
        
        assert self.run.phases[1]["status"] == "running"
        assert self.run.phases[1]["progress"] == 25.0
        assert self.run.phases[1]["message"] == "Processing"
    
    def test_add_log(self):
        """Test adding log entries."""
        self.run.add_log("info", "Retriever", "Found 4 models")
        
        assert len(self.run.logs) == 1
        assert self.run.logs[0]["level"] == "info"
        assert self.run.logs[0]["agent"] == "Retriever"
        assert self.run.logs[0]["message"] == "Found 4 models"
    
    def test_save_checkpoint(self):
        """Test saving checkpoint."""
        checkpoint = {"phase": 1, "score": 0.85}
        self.run.save_checkpoint(checkpoint)
        
        assert self.run.checkpoint == checkpoint
