@echo off
REM MLE-STAR Setup Script for Windows
REM This script sets up the development environment

echo.
echo ========================================
echo MLE-STAR Development Environment Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Creating Python virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/5] Installing Python dependencies...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo [4/5] Installing Node.js dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    cd ..
    pause
    exit /b 1
)
cd ..

echo [5/5] Creating .env file...
if not exist .env (
    (
        echo # LLE Configuration
        echo MODEL_PROVIDER=ollama
        echo MODEL_ID=qwen3:30b
        echo OLLAMA_BASE_URL=http://localhost:11434
        echo.
        echo # Optional: Google Search
        echo # GOOGLE_API_KEY=your_api_key
        echo # GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
        echo.
        echo # Optional: AWS Bedrock
        echo # AWS_REGION=us-east-1
        echo.
        echo # Optional: OpenAI
        echo # OPENAI_API_KEY=your_api_key
    ) > .env
    echo Created .env file with default configuration
) else (
    echo .env file already exists, skipping...
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Start Ollama: ollama serve
echo 2. Start Backend: python -m uvicorn src.mle_star.api.server:app --reload
echo 3. Start Frontend: cd frontend ^& npm run dev
echo.
echo Access the application at http://localhost:3000
echo.
pause
