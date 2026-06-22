param(
    [ValidateSet("simulator", "live")]
    [string]$Connector = "simulator",
    [int]$Hours = 168,
    [int]$Seed = 42,
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if ($Install -or -not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.11 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -e ".[test]"
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
& $Python -m rescue_operator.main --connector $Connector --headless --autonomous --hours $Hours --speed max --seed $Seed
exit $LASTEXITCODE
