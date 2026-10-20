@echo off
REM Build a self-contained Windows binary at dist\KDA.exe (no Python needed to run it).
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip >nul
"%PY%" -m pip install -r requirements-build.txt
"%PY%" -m PyInstaller --clean --noconfirm packaging\kda.spec

echo.
echo Built: %CD%\dist\KDA.exe
endlocal
