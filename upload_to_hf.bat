@echo off
REM Upload Database to HuggingFace Spaces
REM Run this after merging databases

echo.
echo ====================================================
echo   Upload Database to HuggingFace Spaces
echo ====================================================
echo.

REM Change to CallAnalysisApp directory
cd /d "C:\Dev\GitHub\CallAnalysisApp"

REM Run upload script
python upload_to_hf.py

echo.
pause