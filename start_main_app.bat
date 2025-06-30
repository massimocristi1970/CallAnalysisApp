@echo off
REM =================================================================
REM Start Main Call Analysis App
REM Universal launcher - works on any machine with the project files
REM =================================================================

echo ========================================
echo   Starting Call Analysis App
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

REM Check if app.py exists
if not exist "app.py" (
    echo ❌ app.py not found in current directory
    pause
    exit /b 1
)

echo ✅ Found virtual environment
echo ✅ Found app.py

REM Activate virtual environment
call call_analysis_env\Scripts\activate.bat

echo 🚀 Starting Call Analysis App...
echo.
echo The app will open at: http://localhost:8501
echo Press Ctrl+C to stop the app
echo.

REM Start the main app
streamlit run app.py

pause