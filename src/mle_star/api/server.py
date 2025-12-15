"""FastAPI server for MLE-STAR pipeline API.

Provides REST endpoints for:
- Starting pipeline runs
- Querying pipeline status
- Pausing/resuming runs
- Downloading submissions

Also provides WebSocket endpoint for real-time updates.
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import shutil
from pathlib import Path

from mle_star.api.models import (
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global run manager
run_manager: Optional[RunManager] = None

# WebSocket connections by run_id
websocket_connections: dict[str, list[WebSocket]] = {}

# Upload directory
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".csv", ".json", ".parquet", ".xlsx", ".xls", ".zip", ".png", ".jpg", ".jpeg", ".wav", ".mp3"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global run_manager
    run_manager = RunManager()
    # Create upload directory
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("MLE-STAR API server started")
    yield
    logger.info("MLE-STAR API server shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MLE-STAR API",
        description="Machine Learning Engineering Agent via Search and Targeted Refinement",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


app = create_app()


# Helper functions

async def broadcast_to_run(run_id: str, message: WebSocketMessage) -> None:
    """Broadcast a message to all WebSocket connections for a run."""
    if run_id in websocket_connections:
        disconnected = []
        for ws in websocket_connections[run_id]:
            try:
                await ws.send_json(message.model_dump(mode="json"))
            except Exception:
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            websocket_connections[run_id].remove(ws)


def build_status_response(run: PipelineRun) -> PipelineStatusResponse:
    """Build a PipelineStatusResponse from a PipelineRun."""
    phases = []
    
    for phase_num in [1, 2, 3]:
        phase_data = run.phases.get(phase_num, {})
        agents = [
            AgentStatusUpdate(
                agent_id=a["id"],
                agent_name=a["name"],
                status=AgentStatus(a.get("status", "idle")),
                phase=phase_num,
                message=a.get("message"),
                started_at=a.get("started_at"),
                completed_at=a.get("completed_at"),
            )
            for a in phase_data.get("agents", [])
        ]
        
        phases.append(PhaseStatusUpdate(
            phase=phase_num,
            status=PhaseStatus(phase_data.get("status", "pending")),
            progress=phase_data.get("progress", 0.0),
            message=phase_data.get("message"),
            started_at=phase_data.get("started_at"),
            completed_at=phase_data.get("completed_at"),
            agents=agents,
        ))
    
    return PipelineStatusResponse(
        run_id=run.run_id,
        status=run.status,
        current_phase=run.current_phase,
        is_running=run.is_running,
        is_paused=run.is_paused,
        phases=phases,
        current_score=run.current_score,
        best_score=run.best_score,
        current_code=run.current_code,
        error=run.error,
        created_at=run.created_at,
        updated_at=run.updated_at,
        completed_at=run.completed_at,
    )


# REST Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/pipeline/start", response_model=PipelineStartResponse)
async def start_pipeline(
    request: PipelineStartRequest,
    background_tasks: BackgroundTasks,
) -> PipelineStartResponse:
    """Start a new pipeline run."""
    if run_manager is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    # Generate run ID
    run_id = str(uuid.uuid4())[:8]
    
    # Build config
    config_data = request.config.model_dump() if request.config else {}
    config = MLEStarConfig.from_dict(config_data)
    
    # Build task description
    task = TaskDescription(
        description=request.task_description.description,
        task_type=request.task_description.task_type,
        data_modality=request.task_description.data_modality,
        evaluation_metric=request.task_description.evaluation_metric,
        dataset_path=request.dataset_path or request.task_description.dataset_path,
        submission_format=request.task_description.submission_format,
    )
    
    # Create and register run
    run = run_manager.create_run(run_id, task, config)
    
    # Start pipeline in background
    background_tasks.add_task(
        run_pipeline_async,
        run_id,
        task,
        config,
    )
    
    logger.info(f"Pipeline started: {run_id}")
    
    return PipelineStartResponse(
        run_id=run_id,
        status="started",
        message="Pipeline started successfully",
        created_at=run.created_at,
    )


@app.get("/api/pipeline/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(run_id: str) -> PipelineStatusResponse:
    """Get the status of a pipeline run."""
    if run_manager is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return build_status_response(run)


@app.post("/api/pipeline/pause/{run_id}")
async def pause_pipeline(run_id: str):
    """Pause a running pipeline."""
    if run_manager is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    if not run.is_running:
        raise HTTPException(status_code=400, detail="Pipeline is not running")
    
    run.is_paused = True
    run.updated_at = datetime.utcnow()
    
    # Broadcast pause event
    await broadcast_to_run(run_id, WebSocketMessage(
        type="status_update",
        run_id=run_id,
        data={"status": "paused"},
    ))
    
    return {"status": "paused", "run_id": run_id}


@app.post("/api/pipeline/resume/{run_id}")
async def resume_pipeline(run_id: str):
    """Resume a paused pipeline."""
    if run_manager is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    if not run.is_paused:
        raise HTTPException(status_code=400, detail="Pipeline is not paused")
    
    run.is_paused = False
    run.updated_at = datetime.utcnow()
    
    # Broadcast resume event
    await broadcast_to_run(run_id, WebSocketMessage(
        type="status_update",
        run_id=run_id,
        data={"status": "running"},
    ))
    
    return {"status": "resumed", "run_id": run_id}


@app.post("/api/pipeline/stop/{run_id}")
async def stop_pipeline(run_id: str):
    """Stop a running pipeline."""
    if run_manager is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    run.is_running = False
    run.is_paused = False
    run.status = "stopped"
    run.updated_at = datetime.utcnow()
    
    # Broadcast stop event
    await broadcast_to_run(run_id, WebSocketMessage(
        type="status_update",
        run_id=run_id,
        data={"status": "stopped"},
    ))
    
    return {"status": "stopped", "run_id": run_id}


@app.get("/api/submission/download/{run_id}")
async def download_submission(run_id: str):
    """Download the submission file for a completed run."""
    if run_manager is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    run = run_manager.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    if not run.submission_path:
        raise HTTPException(status_code=404, detail="No submission file available")
    
    return FileResponse(
        path=run.submission_path,
        filename=f"submission_{run_id}.csv",
        media_type="text/csv",
    )


@app.get("/api/runs")
async def list_runs(limit: int = 10, offset: int = 0):
    """List recent pipeline runs."""
    if run_manager is None:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    runs = run_manager.list_runs(limit=limit, offset=offset)
    return {
        "runs": [
            {
                "run_id": r.run_id,
                "status": r.status,
                "current_phase": r.current_phase,
                "best_score": r.best_score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
        "total": run_manager.total_runs(),
    }


# File Upload Endpoints

@app.post("/api/datasets/upload")
async def upload_dataset(
    files: list[UploadFile] = File(...),
    run_id: Optional[str] = Form(None),
):
    """Upload dataset files."""
    uploaded_files = []
    errors = []
    
    # Create run-specific directory if run_id provided
    upload_path = UPLOAD_DIR / run_id if run_id else UPLOAD_DIR
    upload_path.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        # Validate file extension
        ext = Path(file.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append({
                "filename": file.filename,
                "error": f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            })
            continue
        
        # Validate file size (max 500MB)
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if size > 500 * 1024 * 1024:  # 500MB
            errors.append({
                "filename": file.filename,
                "error": "File too large. Maximum size is 500MB."
            })
            continue
        
        try:
            # Save file
            file_path = upload_path / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append({
                "filename": file.filename,
                "path": str(file_path),
                "size": size,
                "status": "success"
            })
            logger.info(f"Uploaded file: {file.filename} ({size} bytes)")
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return JSONResponse(content={
        "uploaded": uploaded_files,
        "errors": errors,
        "total_uploaded": len(uploaded_files),
        "total_errors": len(errors),
    })


@app.get("/api/datasets/list")
async def list_datasets(run_id: Optional[str] = None):
    """List uploaded dataset files."""
    upload_path = UPLOAD_DIR / run_id if run_id else UPLOAD_DIR
    
    if not upload_path.exists():
        return {"files": [], "total": 0}
    
    files = []
    for file_path in upload_path.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    
    return {"files": files, "total": len(files)}


@app.delete("/api/datasets/{filename}")
async def delete_dataset(filename: str, run_id: Optional[str] = None):
    """Delete an uploaded dataset file."""
    upload_path = UPLOAD_DIR / run_id if run_id else UPLOAD_DIR
    file_path = upload_path / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    
    try:
        file_path.unlink()
        return {"status": "deleted", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoint

@app.websocket("/ws/pipeline/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for real-time pipeline updates."""
    await websocket.accept()
    
    # Register connection
    if run_id not in websocket_connections:
        websocket_connections[run_id] = []
    websocket_connections[run_id].append(websocket)
    
    logger.info(f"WebSocket connected for run {run_id}")
    
    try:
        # Send initial status
        if run_manager:
            run = run_manager.get_run(run_id)
            if run:
                status = build_status_response(run)
                await websocket.send_json({
                    "type": "initial_status",
                    "run_id": run_id,
                    "data": status.model_dump(mode="json"),
                    "timestamp": datetime.utcnow().isoformat(),
                })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for run {run_id}")
    finally:
        # Unregister connection
        if run_id in websocket_connections:
            if websocket in websocket_connections[run_id]:
                websocket_connections[run_id].remove(websocket)


# Background task for running pipeline

async def run_pipeline_async(
    run_id: str,
    task: TaskDescription,
    config: MLEStarConfig,
) -> None:
    """Run the pipeline asynchronously and broadcast updates."""
    from mle_star.orchestrator import MLEStarOrchestrator
    
    if run_manager is None:
        return
    
    run = run_manager.get_run(run_id)
    if run is None:
        return
    
    try:
        # Create orchestrator
        orchestrator = MLEStarOrchestrator(config=config)
        
        # Update run status
        run.is_running = True
        run.status = "running"
        run.current_phase = 1
        
        # Broadcast start
        await broadcast_to_run(run_id, WebSocketMessage(
            type="pipeline_started",
            run_id=run_id,
            data={"phase": 1},
        ))
        
        # Run the pipeline
        result = await orchestrator.run(task, generate_submission=True)
        
        # Update run with results
        run.is_running = False
        run.status = "completed" if not result.error else "error"
        run.error = result.error
        run.current_code = result.final_solution
        run.best_score = result.final_score
        run.current_score = result.final_score
        run.completed_at = datetime.utcnow()
        
        if result.submission_result:
            run.submission_path = result.submission_result.submission_path
        
        # Broadcast completion
        await broadcast_to_run(run_id, WebSocketMessage(
            type="pipeline_completed",
            run_id=run_id,
            data={
                "status": run.status,
                "score": run.best_score,
                "error": run.error,
            },
        ))
        
        logger.info(f"Pipeline {run_id} completed with score {run.best_score}")
        
    except Exception as e:
        logger.exception(f"Pipeline {run_id} failed: {e}")
        run.is_running = False
        run.status = "error"
        run.error = str(e)
        run.completed_at = datetime.utcnow()
        
        await broadcast_to_run(run_id, WebSocketMessage(
            type="pipeline_error",
            run_id=run_id,
            data={"error": str(e)},
        ))


# Entry point for running the server directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
