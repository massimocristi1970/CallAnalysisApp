@echo off
title Call Analysis Dashboard
echo Starting Call Analysis Dashboard...
echo.

REM Change to the specific project directory
cd /d "C:\Users\Administrator\OneDrive\Documenten\CallAnalysisApp"

REM Show current directory for debugging
echo Current directory: %cd%
echo.

REM Check if dashboard.py exists
if not exist "dashboard.py" (
    echo ERROR: dashboard.py not found!
    echo Looking in: %cd%
    echo Files in this directory:
    dir *.py
    pause
    exit /b 1
)

REM Start the Dashboard on port 8503
echo Starting Dashboard on port 8503...
echo.
echo The dashboard will open in your browser automatically.
echo Dashboard URL: http://localhost:8503
echo.
echo To stop the dashboard, press Ctrl+C in this window.
echo.
streamlit run dashboard.py --server.port 8503

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo An error occurred starting the dashboard.
    pause
)