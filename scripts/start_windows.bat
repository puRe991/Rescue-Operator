@echo off
setlocal enabledelayedexpansion
set CONNECTOR=%~1
if "%CONNECTOR%"=="" set CONNECTOR=simulator
set HOURS=%~2
if "%HOURS%"=="" set HOURS=168
set SEED=%~3
if "%SEED%"=="" set SEED=42

set REPO_ROOT=%~dp0..
cd /d "%REPO_ROOT%"

if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv || exit /b 1
  .venv\Scripts\python.exe -m pip install --upgrade pip || exit /b 1
  .venv\Scripts\python.exe -m pip install -e ".[test]" || exit /b 1
)

.venv\Scripts\python.exe -m rescue_operator.main --connector %CONNECTOR% --headless --autonomous --hours %HOURS% --speed max --seed %SEED%
exit /b %ERRORLEVEL%
