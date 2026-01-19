@echo off
REM MLE-STAR Agent Startup Script
REM This script activates the virtual environment, starts the backend API server,
REM and launches the frontend in the default browser

echo ========================================
echo Starting MLE-STAR Agent System
echo ========================================
echo.

REM Check if Lemonade server is running
echo [0/5] Checking Lemonade server status...
curl -s http://localhost:8080/health >nul 2>&1
if errorlevel 1 (
    curl -s http://localhost:8080/v1/models >nul 2>&1
    if errorlevel 1 (
        echo WARNING: Lemonade server is not running at http://localhost:8080
        echo Please start your llama.cpp server with Qwen3 Next 72B model
        echo.
        echo Press any key to continue anyway, or Ctrl+C to exit...
        pause >nul
    ) else (
        echo Lemonade server is running!
        echo Using Qwen3 Next 72B model
    )
) else (
    echo Lemonade server is running!
    echo Using Qwen3 Next 72B model
)
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at .venv
    echo Please run: python -m venv .venv
    echo Then install dependencies: pip install -e .
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/5] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo [2/5] Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
) else (
    echo [2/5] Frontend dependencies already installed
)

REM Start backend server in a new window
echo [3/5] Starting backend API server on port 8000...
echo Using Lemonade with Qwen3 Next 72B model
start "MLE-STAR Backend (Qwen3 Next 72B)" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn src.mle_star.api.server:app --host 0.0.0.0 --port 8000"

REM Wait a few seconds for backend to start
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Start frontend in a new window
echo [4/5] Starting frontend on port 3000...
start "MLE-STAR Frontend" cmd /k "cd frontend && npm run dev"

REM Wait for frontend to start
echo Waiting for frontend to initialize...
timeout /t 8 /nobreak >nul

REM Open browser
echo [5/5] Opening browser...
echo.
echo ========================================
echo MLE-STAR Agent System is running!
echo ========================================
echo.
echo Model: Qwen3 Next 72B (Lemonade/llama.cpp)
echo Lemonade Server: http://localhost:8080
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo You can change the model in the Configuration panel
echo in the web interface.
echo.
echo Press any key to open the browser...
pause >nul

start http://localhost:3000

echo.
echo ========================================
echo System Started Successfully!
echo ========================================
echo.
echo To stop the system:
echo 1. Close the "MLE-STAR Backend (Qwen3 Next 72B)" window
echo 2. Close the "MLE-STAR Frontend" window
echo.
echo This window can be closed safely.
pause
