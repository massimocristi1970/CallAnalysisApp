@echo off
title Call Analysis App
echo Starting Call Analysis App...
echo.

REM Change to the specific project directory
cd /d "C:\Dev\GitHub\CallAnalysisApp"

REM Show current directory for debugging
echo Current directory: %cd%
echo.

REM Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found!
    echo Looking in: %cd%
    echo Files in this directory:
    dir *.py
    pause
    exit /b 1
)

REM Start the Streamlit app
echo Starting Main Call Analysis App...
echo.
echo The app will open in your browser automatically.
echo Main App URL: http://localhost:8501
echo.
echo To stop the app, press Ctrl+C in this window.
echo.
streamlit run app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo An error occurred starting the app.
    pause
)