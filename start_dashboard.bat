@echo off
REM =================================================================
REM Start Performance Dashboard
REM Universal launcher - works on any machine with the project files
REM =================================================================

echo ========================================
echo   Starting Performance Dashboard
echo ========================================

REM Get the directory where this batch file is located
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM Check if virtual environment exists
if not exist "call_analysis_env\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please run setup first or check installation
    pause
    exit /b 1
)

REM Check if dashboard.py exists
if not exist "dashboard.py" (
    echo ❌ dashboard.py not found in current directory
    pause
    exit /b 1
)

echo ✅ Found virtual environment
echo ✅ Found dashboard.py

REM Activate virtual environment
call call_analysis_env\Scripts\activate.bat

echo 📊 Starting Performance Dashboard...
echo.
echo The dashboard will open at: http://localhost:8503
echo Press Ctrl+C to stop the dashboard
echo.

REM Start the dashboard on port 8503
streamlit run dashboard.py --server.port 8503

pause