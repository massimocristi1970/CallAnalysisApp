@echo off
REM Merge Hugging Face Database into Local Database
REM Double-click this file to run the merge tool

echo.
echo ====================================================
echo   Call Analysis Database Merger
echo ====================================================
echo.
echo This will merge a downloaded Hugging Face database
echo into your local call_analysis. db file
echo.
echo A file picker will open - select the downloaded . db file
echo from your Downloads folder
echo.
pause

REM Change to the script directory
cd /d "%~dp0"

REM Run the merge script with Python
python "%~dp0merge_databases.py"


echo.
echo ====================================================
echo   Merge Complete
echo ====================================================
echo.
pause