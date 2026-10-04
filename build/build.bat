@echo off
:: Builds the app folder and the installer in one go. No prompts.
:: Output: dist\WhisperWriter-<version>\  and  dist\installer\WhisperWriter_Setup_<version>.exe
setlocal
cd /d "%~dp0.."
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv not found. Create it and pip install -r requirements.txt -r requirements-build.txt
    exit /b 1
)
"venv\Scripts\python.exe" -m pip show pyinstaller >nul 2>&1 || "venv\Scripts\python.exe" -m pip install -r requirements-build.txt
"venv\Scripts\python.exe" build\build.py %*
exit /b %errorlevel%
