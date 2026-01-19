@echo off
REM MLE-STAR Backend Runner
REM Starts the FastAPI backend server

echo.
echo ========================================
echo MLE-STAR Backend Server
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found
    echo Creating default .env file...
    (
        echo MODEL_PROVIDER=ollama
        echo MODEL_ID=qwen3:30b
        echo OLLAMA_BASE_URL=http://localhost:11434
    ) > .env
)

echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn src.mle_star.api.server:app --reload --host 0.0.0.0 --port 8000

pause
