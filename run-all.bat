@echo off
REM MLE-STAR All Services Runner
REM Starts all services in separate windows

echo.
echo ========================================
echo MLE-STAR - Starting All Services
echo ========================================
echo.

REM Check if virtual environment exists
if not exist .venv (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Starting services...
echo.

REM Start Backend in new window
echo [1/2] Starting Backend Server...
start "MLE-STAR Backend" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn src.mle_star.api.server:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak

REM Start Frontend in new window
echo [2/2] Starting Frontend Server...
start "MLE-STAR Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo All Services Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the command windows to stop the services
echo.
pause
