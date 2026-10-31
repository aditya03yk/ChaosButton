# ChaosButton setup for Windows PowerShell.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

foreach ($tool in "python", "node", "npm") {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Missing required tool: $tool" }
}
python -m venv .venv
.\.venv\Scripts\pip install --quiet --upgrade pip
.\.venv\Scripts\pip install --quiet -r requirements.txt -r demo_shop\requirements.txt
Push-Location frontend; npm install; Pop-Location
if (-not (Test-Path .env)) { Copy-Item .env.example .env }

Push-Location backend
..\.venv\Scripts\python -c "from app.core.config import get_settings; from app.storage import database; database.configure(get_settings().database_url); print('Database initialised')"
Pop-Location

try { Invoke-RestMethod http://localhost:11434/api/tags | Out-Null; Write-Host "Ollama is running." }
catch {
    Write-Host "Ollama is not running. Install it from https://ollama.com, then run:"
    Write-Host "  ollama serve"
    Write-Host "  ollama pull gemma3:4b"
}
Write-Host "Setup complete. Start everything with: scripts\start.ps1"
