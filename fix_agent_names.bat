@echo off
REM Fix Agent Name Misspellings
REM Merges misspelled agent names into correct names

echo.
echo ====================================================
echo   Agent Name Correction Tool
echo ====================================================
echo.

REM Change to CallAnalysisApp directory
cd /d "C:\Dev\GitHub\CallAnalysisApp"

REM Run the correction script
python fix_agent_names.py

echo.
echo ====================================================
echo   Correction Complete
echo ====================================================
echo.
pause