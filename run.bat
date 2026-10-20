@echo off
REM Launch KDA (native Qt desktop app) on Windows.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

set "PY=.venv\Scripts\python.exe"
"%PY%" -c "import fastapi, uvicorn, httpx" >nul 2>&1
if errorlevel 1 (
    "%PY%" -m pip install --upgrade pip >nul 2>&1
    "%PY%" -m pip install -r requirements.txt
)

set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
"%PY%" -m kda %*
endlocal
