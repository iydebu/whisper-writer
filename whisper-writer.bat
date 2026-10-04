@echo off
set "ROOT=%~dp0"
cd /d "%ROOT%"
set "PY=%ROOT%venv\Scripts\python.exe"
if exist "%PY%" (
    call "%ROOT%venv\Scripts\activate.bat"
    "%PY%" "%ROOT%run.py"
) else (
    python "%ROOT%run.py"
)
if errorlevel 1 (
    echo WhisperWriter exited with an error.
    pause
)
exit /b
