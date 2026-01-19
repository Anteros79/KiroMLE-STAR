@echo off
REM MLE-STAR Frontend Runner
REM Starts the Next.js frontend development server

echo.
echo ========================================
echo MLE-STAR Frontend Server
echo ========================================
echo.

cd frontend

echo Starting Next.js development server on http://localhost:3000
echo Press Ctrl+C to stop the server
echo.

call npm run dev

pause
