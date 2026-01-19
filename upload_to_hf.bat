@echo off
REM Upload Database to HuggingFace Spaces
REM Run this after merging databases

echo.
echo ====================================================
echo   Upload Database to HuggingFace Spaces
echo ====================================================
echo.

REM Change to the script directory (works from any location)
cd /d "%~dp0"

REM Run upload script
python "%~dp0upload_to_hf.py"

echo.
pause