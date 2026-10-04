@echo off
setlocal enabledelayedexpansion
title WhisperWriter Smart Installer
color 0A

echo.
echo ============================================================
echo   WhisperWriter Smart Installer
echo ============================================================
echo.

:: Check if Python is installed and find best version (prefer 3.11/3.12)
echo [1/6] Checking Python installation...

set PYTHON_CMD=
set PYTHON_VERSION=

:: Try to find Python 3.11 or 3.12 first (best compatibility)
for %%v in (3.12 3.11 3.10) do (
    if not defined PYTHON_CMD (
        py -%%v --version >nul 2>&1
        if not errorlevel 1 (
            set PYTHON_CMD=py -%%v
            for /f "tokens=2 delims= " %%x in ('py -%%v --version 2^>^&1') do set PYTHON_VERSION=%%x
        )
    )
)

:: Fallback to default python
if not defined PYTHON_CMD (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [ERROR] Python is not installed or not in PATH!
        echo.
        echo Please install Python 3.10, 3.11, or 3.12 from:
        echo   https://www.python.org/downloads/
        echo.
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
)

echo   Found Python %PYTHON_VERSION%
echo   Using: %PYTHON_CMD%

:: Check Python version is 3.10-3.12
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)
if %MAJOR% LSS 3 (
    echo [ERROR] Python 3.10-3.12 required. Found Python %PYTHON_VERSION%
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 10 (
    echo [ERROR] Python 3.10-3.12 required. Found Python %PYTHON_VERSION%
    pause
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% GEQ 13 (
    echo.
    echo [ERROR] Python %PYTHON_VERSION% is too new - packages don't have wheels yet!
    echo.
    echo Please install Python 3.11 or 3.12 from:
    echo   https://www.python.org/downloads/release/python-3119/
    echo.
    pause
    exit /b 1
)
echo   [OK] Python version compatible
echo.

:: Detect GPU
echo [2/6] Detecting GPU...
set GPU_TYPE=NONE
set GPU_NAME=None
set GPU_VRAM=0

:: Check for NVIDIA GPU
for /f "tokens=*" %%g in ('wmic path win32_VideoController get Name 2^>nul ^| findstr /i "NVIDIA"') do (
    set GPU_TYPE=NVIDIA
    set GPU_NAME=%%g
)

:: Check for AMD GPU
if "%GPU_TYPE%"=="NONE" (
    for /f "tokens=*" %%g in ('wmic path win32_VideoController get Name 2^>nul ^| findstr /i "AMD Radeon"') do (
        set GPU_TYPE=AMD
        set GPU_NAME=%%g
    )
)

:: Check for Intel GPU
if "%GPU_TYPE%"=="NONE" (
    for /f "tokens=*" %%g in ('wmic path win32_VideoController get Name 2^>nul ^| findstr /i "Intel"') do (
        set GPU_TYPE=INTEL
        set GPU_NAME=%%g
    )
)

:: Get VRAM for NVIDIA
if "%GPU_TYPE%"=="NVIDIA" (
    for /f "skip=1 tokens=*" %%v in ('nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2^>nul') do (
        set /a GPU_VRAM=%%v
    )
)

if "%GPU_TYPE%"=="NONE" (
    echo   No dedicated GPU detected - will use CPU
) else (
    echo   Detected: %GPU_NAME%
    if %GPU_VRAM% GTR 0 (
        echo   VRAM: %GPU_VRAM% MB
    )
)
echo.

:: Check RAM
echo [3/6] Checking system RAM...
for /f "skip=1 tokens=*" %%m in ('wmic ComputerSystem get TotalPhysicalMemory 2^>nul') do (
    set /a RAM_BYTES=%%m 2>nul
    if !RAM_BYTES! GTR 0 (
        set /a RAM_GB=!RAM_BYTES!/1073741824
    )
)
:: Fallback calculation using PowerShell if wmic fails
if "%RAM_GB%"=="" (
    for /f %%m in ('powershell -command "[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)"') do set RAM_GB=%%m
)
echo   Total RAM: %RAM_GB% GB
echo.

:: Check CPU cores
echo [4/6] Checking CPU...
for /f "tokens=*" %%c in ('wmic cpu get Name 2^>nul ^| findstr /v "Name" ^| findstr /r "[A-Za-z]"') do set CPU_NAME=%%c
for /f %%n in ('wmic cpu get NumberOfCores 2^>nul ^| findstr /r "[0-9]"') do set CPU_CORES=%%n
for /f %%t in ('wmic cpu get NumberOfLogicalProcessors 2^>nul ^| findstr /r "[0-9]"') do set CPU_THREADS=%%t
echo   CPU: %CPU_NAME%
echo   Cores: %CPU_CORES%  Threads: %CPU_THREADS%
echo.

:: Check disk space
echo [5/6] Checking disk space...
for /f "tokens=3" %%d in ('dir /-c "%~dp0" 2^>nul ^| findstr /c:"bytes free"') do set DISK_FREE=%%d
set /a DISK_GB=%DISK_FREE:~0,-9%
if %DISK_GB% LSS 1 set DISK_GB=1
echo   Free disk space: ~%DISK_GB% GB
echo.

:: Generate recommendations
echo ============================================================
echo   HARDWARE ANALYSIS COMPLETE
echo ============================================================
echo.

:: Determine recommended model quality
set RECOMMENDED_MODEL=balanced
set MODEL_REASON=

:: RAM-based recommendations
if %RAM_GB% LSS 4 (
    set RECOMMENDED_MODEL=fast
    set MODEL_REASON=Limited RAM ^(%RAM_GB% GB^)
) else if %RAM_GB% LSS 8 (
    set RECOMMENDED_MODEL=balanced
    set MODEL_REASON=Moderate RAM ^(%RAM_GB% GB^)
) else if %RAM_GB% GEQ 16 (
    if "%GPU_TYPE%"=="NVIDIA" (
        if %GPU_VRAM% GEQ 6000 (
            set RECOMMENDED_MODEL=best
            set MODEL_REASON=High VRAM ^(%GPU_VRAM% MB^) + adequate RAM
        ) else if %GPU_VRAM% GEQ 4000 (
            set RECOMMENDED_MODEL=quality
            set MODEL_REASON=Good VRAM ^(%GPU_VRAM% MB^)
        ) else (
            set RECOMMENDED_MODEL=balanced
            set MODEL_REASON=Limited VRAM ^(%GPU_VRAM% MB^)
        )
    ) else (
        set RECOMMENDED_MODEL=quality
        set MODEL_REASON=Good RAM ^(%RAM_GB% GB^), no NVIDIA GPU
    )
) else (
    set RECOMMENDED_MODEL=balanced
    set MODEL_REASON=Standard configuration
)

:: CPU-only mode warning
set USE_CPU=no
if "%GPU_TYPE%"=="NONE" set USE_CPU=yes
if "%GPU_TYPE%"=="AMD" set USE_CPU=yes
if "%GPU_TYPE%"=="INTEL" set USE_CPU=yes

echo   RECOMMENDATIONS:
echo   ----------------
echo.
echo   Model Quality: %RECOMMENDED_MODEL%
echo   Reason: %MODEL_REASON%
echo.

if "%USE_CPU%"=="yes" (
    echo   [!] No NVIDIA GPU detected - will run on CPU
    echo       This is slower but fully functional.
    echo       Consider using 'fast' or 'balanced' models.
    echo.
) else (
    echo   [OK] NVIDIA GPU detected - CUDA acceleration enabled
    echo       Transcription will be much faster!
    echo.
)

:: Model size reference
echo   MODEL REFERENCE (English mode):
echo   -------------------------------
echo   fast     - tiny.en   ^(~75MB^)  - Fastest, basic accuracy
echo   balanced - base.en   ^(~150MB^) - Good speed/accuracy balance
echo   quality  - small.en  ^(~500MB^) - Better accuracy, slower
echo   best     - medium.en ^(~1.5GB^) - Best accuracy, slowest
echo.
echo   LANGUAGE MODES:
echo   ---------------
echo   english        - English speech to English text
echo   indian_english - Indian-accented English (uses custom model)
echo   hinglish       - Hindi speech to English text (translation)
echo.

:: Check disk space warning
if %DISK_GB% LSS 3 (
    echo   [WARNING] Low disk space! At least 3GB recommended.
    echo.
)

echo ============================================================
echo.

:: ============================================================
:: AUTO-CONFIGURE src/config.yaml BASED ON HARDWARE
:: ============================================================

:: Determine device and compute type based on hardware
set DEVICE_SETTING=cpu
set COMPUTE_TYPE=int8

if "%GPU_TYPE%"=="NVIDIA" (
    set DEVICE_SETTING=auto
    if %GPU_VRAM% GEQ 6000 (
        if %RAM_GB% GEQ 16 (
            set COMPUTE_TYPE=float16
        ) else (
            set COMPUTE_TYPE=int8_float16
        )
    ) else if %GPU_VRAM% GEQ 4000 (
        set COMPUTE_TYPE=int8_float16
    ) else (
        set COMPUTE_TYPE=int8_float16
    )
)

:: Generate config.yaml with optimal settings
echo Generating optimized config.yaml...
echo model_options: > src\config.yaml
echo   model_quality: %RECOMMENDED_MODEL% >> src\config.yaml
echo   language_mode: english >> src\config.yaml
echo   device: %DEVICE_SETTING% >> src\config.yaml
echo   compute_type: %COMPUTE_TYPE% >> src\config.yaml
echo. >> src\config.yaml
echo recording_options: >> src\config.yaml
echo   activation_key: f2 >> src\config.yaml
echo   sound_enabled: true >> src\config.yaml
echo   start_minimized: false >> src\config.yaml
echo   run_on_startup: false >> src\config.yaml
echo   enable_streaming: false >> src\config.yaml
echo. >> src\config.yaml
echo post_processing: >> src\config.yaml
echo   remove_trailing_period: false >> src\config.yaml
echo   add_space_after: false >> src\config.yaml
echo   remove_capitalization: false >> src\config.yaml
echo [OK] Config saved to src\config.yaml
echo.

echo [6/6] Installing dependencies...
echo.

:: Create virtual environment
echo Creating virtual environment...
%PYTHON_CMD% -m venv venv
call venv\Scripts\activate.bat
echo Virtual environment created and activated.
echo.

:: Upgrade pip
echo Upgrading pip...
pip install --upgrade pip

:: Install requirements
echo.
echo Installing WhisperWriter dependencies...
pip install -r requirements.txt --only-binary av

:: Note: faster-whisper uses ctranslate2 which auto-detects CUDA
if "%GPU_TYPE%"=="NVIDIA" (
    echo.
    echo [INFO] NVIDIA GPU detected - ctranslate2 will use CUDA automatically
    echo        Make sure NVIDIA CUDA drivers are installed.
)

echo.
echo ============================================================
echo   DOWNLOADING WHISPER MODELS
echo ============================================================
echo.

:: Download Medium English model (best quality English)
echo [Model 1/3] Downloading Medium English model (medium.en)...
echo             This provides the best English transcription quality.
echo             Size: ~1.5GB - please wait...
echo.
python -c "from faster_whisper import WhisperModel; print('Downloading medium.en...'); m = WhisperModel('medium.en', device='cpu', compute_type='int8'); print('Medium English model ready!')"
if errorlevel 1 (
    echo [WARNING] Failed to download medium.en model. You can download it later on first use.
) else (
    echo [OK] Medium English model downloaded successfully!
)
echo.

:: Download Small multilingual model (for Hindi->English translation)
echo [Model 2/3] Downloading Small multilingual model (small)...
echo             Used for Hindi/Hinglish to English translation.
echo             Size: ~500MB - please wait...
echo.
python -c "from faster_whisper import WhisperModel; print('Downloading small...'); m = WhisperModel('small', device='cpu', compute_type='int8'); print('Small multilingual model ready!')"
if errorlevel 1 (
    echo [WARNING] Failed to download small model. You can download it later on first use.
) else (
    echo [OK] Small multilingual model downloaded successfully!
)
echo.

:: Download and convert Indian English model
echo [Model 3/3] Downloading Indian English model (Oriserve/Whisper-Hindi2Hinglish-Apex)...
echo             This model is optimized for Indian English accents.
echo             Size: ~3GB - please wait...
echo.

set INDIAN_MODEL_PATH=%~dp0models\whisper-hindi2hinglish-apex

if exist "%INDIAN_MODEL_PATH%" (
    echo [OK] Indian English model already exists, skipping download.
) else (
    python -m ctranslate2.converters.transformers --model Oriserve/Whisper-Hindi2Hinglish-Apex --output_dir "%INDIAN_MODEL_PATH%" --quantization float16 --copy_files tokenizer.json preprocessor_config.json
    if errorlevel 1 (
        echo [WARNING] Failed to download Indian English model.
        echo          You can run 'python models\setup_indian_english.py' later.
    ) else (
        echo [OK] Indian English model downloaded and converted successfully!
    )
)
echo.

echo ============================================================
echo   INSTALLATION COMPLETE - AUTO-CONFIGURED!
echo ============================================================
echo.
echo   YOUR HARDWARE:
echo   - GPU: %GPU_NAME% ^(%GPU_VRAM% MB VRAM^)
echo   - RAM: %RAM_GB% GB
echo   - CPU: %CPU_NAME% ^(%CPU_CORES% cores^)
echo.
echo   AUTO-CONFIGURED FOR OPTIMAL PERFORMANCE:
echo   - Model Quality: %RECOMMENDED_MODEL%
if "%USE_CPU%"=="yes" (
    echo   - Device: cpu ^(CPU inference^)
) else (
    echo   - Device: %DEVICE_SETTING% ^(GPU acceleration enabled^)
)
echo   - Compute Type: %COMPUTE_TYPE%
echo   - Activation Key: F2
echo.
echo   Config saved to: src\config.yaml
echo   ^(Edit settings anytime via the app's Settings menu^)
echo.
echo   PRE-DOWNLOADED MODELS ^(~5GB total^):
echo   - medium.en   ^(~1.5GB^) - Best English transcription
echo   - small       ^(~500MB^) - Hindi to English translation
echo   - Indian English ^(~3GB^) - Indian accent support
echo.
echo   READY TO USE:
echo   - Double-click: whisper-writer.bat
echo   - Or run: venv\Scripts\python.exe src\main.py
echo ============================================================
echo.
pause
