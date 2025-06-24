@echo off
REM Change directory to your app folder
cd /d C:\CallAnalysisApp

REM Activate virtual environment
call venv\Scripts\activate

REM OPTIONAL: Install core packages if needed (safe to run each time)
pip install --upgrade pip
pip install -r requirements.txt

REM Run the Streamlit app
streamlit run app.py

REM Pause in case of error
pause
