@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo   AEOForge - Automated Local Setup & Launch Engine (Windows)
echo   Autonomous Meta AI Web Agent & AEO Auditor
echo ==============================================================================

cd /d "%~dp0"

:: 1. Check Python installation
echo.
echo [1/5] Checking Python runtime environment...
set "PY_CMD="
for %%C in (python py -3 python3) do (
    if not defined PY_CMD (
        %%C --version >nul 2>&1
        if !errorlevel! equ 0 (
            set "PY_CMD=%%C"
        )
    )
)

if not defined PY_CMD (
    echo Error: Python 3.10 or higher is required. Please install Python from python.org.
    exit /b 1
)
echo Found Python command: %PY_CMD%

:: 2. Setup Virtual Environment
echo.
echo [2/5] Initializing isolated Python virtual environment...
if not exist ".venv" (
    echo Creating virtual environment at .venv...
    %PY_CMD% -m venv .venv
    if !errorlevel! neq 0 (
        echo Failed to create virtual environment.
        exit /b 1
    )
)
echo Virtual environment ready at .venv.

set "VENV_PY=.venv\Scripts\python.exe"
set "VENV_PIP=.venv\Scripts\pip.exe"

:: 3. Install dependencies
echo.
echo [3/5] Installing dependencies and AEOForge package...
%VENV_PIP% install --upgrade pip setuptools wheel >nul 2>&1
%VENV_PIP% install -e .
if !errorlevel! neq 0 (
    echo Error installing dependencies.
    exit /b 1
)

:: 4. Install Playwright browser
echo.
echo [4/5] Installing Playwright Chromium browser...
%VENV_PY% -m playwright install chromium
if !errorlevel! neq 0 (
    echo Warning during Playwright installation. Continuing...
)

:: 5. Create data directory
if not exist "data" mkdir "data"

echo.
echo ==============================================================================
echo AEOForge environment is ready!
echo ==============================================================================

:: Handle arguments
set "ACTION=%~1"
set "PORT=%~2"
if "%PORT%"=="" set "PORT=8000"

if "%ACTION%"=="--start" goto do_start
if "%ACTION%"=="start" goto do_start
if "%ACTION%"=="serve" goto do_start
if "%ACTION%"=="--test" goto do_test
if "%ACTION%"=="test" goto do_test
if "%ACTION%"=="--audit" goto do_audit
if "%ACTION%"=="audit" goto do_audit

echo.
echo Quick Command Reference:
echo   • Launch Web Dashboard:  setup.bat --start
echo   • Run CLI Audit:         setup.bat --audit https://example.com
echo   • Run Test Suite:        setup.bat --test
goto :eof

:do_start
echo Launching AEOForge Web UI on http://127.0.0.1:%PORT%...
start http://127.0.0.1:%PORT%
%VENV_PY% -m uvicorn aeoforge.main:app --host 127.0.0.1 --port %PORT% --reload
goto :eof

:do_test
%VENV_PY% -m pytest -v
goto :eof

:do_audit
if "%~2"=="" (
    echo Error: Please specify a URL to audit. Example: setup.bat --audit https://example.com
    exit /b 1
)
%VENV_PY% -m aeoforge.cli audit %~2
goto :eof
