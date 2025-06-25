@echo off
title Call Analysis App
echo Starting Call Analysis App...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "call_analysis_312\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create virtual environment first: python -m venv call_analysis_312
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call call_analysis_312\Scripts\activate

REM Check if app.py exists
if not exist "app.py" (
    echo ERROR: app.py not found!
    echo Make sure you're in the correct directory.
    pause
    exit /b 1
)

REM Start the Streamlit app
echo Starting Streamlit app...
echo.
echo The app will open in your browser automatically.
echo To stop the app, press Ctrl+C in this window.
echo.
streamlit run app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo An error occurred starting the app.
    pause
)