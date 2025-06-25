@echo off
title Call Analysis Dashboard
echo Starting Call Analysis Dashboard...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if dashboard.py exists
if not exist "dashboard.py" (
    echo ERROR: dashboard.py not found!
    echo Make sure you're in the correct directory.
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