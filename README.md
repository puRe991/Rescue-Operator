# Rescue Operator AI

Autonomous AI prototype for Rescue Operator-style emergency dispatch. The current runnable backend is a local simulator; a live connector is separated behind an authorization boundary so a future official integration can target `https://game.rescue-operator.com` without coupling planning logic to transport details.

## Features

- Pydantic domain models for stations, vehicles, personnel, missions, hospitals and economy.
- Safety layer validating crew, qualifications/modules, water, breathing air, vehicle condition, double assignment, liquidity reserve and loan sustainability.
- Tactical dispatcher with an OR-Tools integration surface and safety-filtered rolling assignments.
- Event simulator with random missions, failures/deadlines and structured JSONL decision logs.
- Gymnasium environment and PPO training entry point.
- Hybrid agent that falls back to the deterministic rule-based dispatcher when learned actions are unavailable or unsafe.
- Watchdog that persists invalid/stuck states and continues with fallback logic.
- Connector abstraction for simulator-backed runs and Playwright-based live UI control for authorized game integrations.
- Browser screen perception through DOM text, accessibility tree, screenshots and optional OCR (`pytesseract`).

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
```

Dependencies such as OR-Tools, PySide6, Playwright, Pillow, pytesseract and Stable-Baselines3 are declared in `pyproject.toml`. For live browser control, install the browser runtime with `playwright install chromium`; for OCR install the Tesseract binary on the host.


## Windows start

PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\start_windows.ps1 -Install -Connector simulator -Hours 168 -Seed 42
```

Command Prompt:

```bat
scripts\start_windows.bat simulator 168 42
```

After installation you can also run the packaged entrypoint:

```powershell
.\.venv\Scripts\rescue-operator-ai.exe --connector simulator --headless --autonomous --hours 168 --speed max --seed 42
```

See `scripts/README_WINDOWS.md` for live connector and OCR notes.

## Headless run

```bash
python -m src.main --headless --autonomous --hours 168 --speed max --seed 42
```

Outputs are written to `runs/decisions.jsonl` and `runs/final_state.json`.


## Authorized live browser run

Set credentials only if the operator account is authorized for automation:

```bash
export RESCUE_OPERATOR_USERNAME=...
export RESCUE_OPERATOR_PASSWORD=...
python -m src.main --connector live --headless --autonomous --hours 168 --speed max --seed 42
```

The live connector reads state from `window.__RESCUE_OPERATOR_STATE__` or the configured `#rescue-operator-state` JSON element, maps validated actions to configured UI selectors, captures screenshots, reads DOM/accessibility text and adds optional OCR text to each live action log.

## Configuration and assumptions

Default assumptions live in `config/default.yaml`. The simulator remains the default execution target. Live play uses Playwright UI selectors against `https://game.rescue-operator.com`; the code does not implement private API probing, CAPTCHA bypass or anti-cheat circumvention.

## Tests

```bash
pytest
```
