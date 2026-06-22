# Windows start

## PowerShell (recommended)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\start_windows.ps1 -Install -Connector simulator -Hours 168 -Seed 42
```

## Command Prompt

```bat
scripts\start_windows.bat simulator 168 42
```

## Live browser connector

Install Playwright's Chromium runtime once after the Python environment exists:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
$env:RESCUE_OPERATOR_USERNAME="..."
$env:RESCUE_OPERATOR_PASSWORD="..."
.\scripts\start_windows.ps1 -Connector live -Hours 168 -Seed 42
```

OCR needs the Tesseract Windows binary installed separately and available on `PATH`.
