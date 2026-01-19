@echo off
REM MLE-STAR Test Runner
REM Runs all tests

echo.
echo ========================================
echo MLE-STAR Test Suite
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo Running all tests...
echo.

python -m pytest tests/ -v --tb=short

echo.
echo ========================================
echo Test Run Complete
echo ========================================
echo.

pause
