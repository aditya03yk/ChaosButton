# Starts all ChaosButton services in separate windows. Close the windows to stop them.
$ErrorActionPreference = "Stop"
$root = Join-Path $PSScriptRoot ".."
$py = Join-Path $root ".venv\Scripts\python.exe"

function Launch($name, $dir, $file, $arguments) {
    Start-Process -FilePath $file -ArgumentList $arguments -WorkingDirectory (Join-Path $root $dir) -WindowStyle Minimized
    Write-Host "started $name"
}

Launch "inventory" "demo_shop" $py "-m uvicorn inventory_service:app --port 9100"
Launch "backend"   "backend"   $py "-m uvicorn app.main:app --host 127.0.0.1 --port 8000"
Launch "weak shop" "demo_shop" $py "-m uvicorn weak_app:app --port 9001"
Launch "resilient" "demo_shop" $py "-m uvicorn resilient_app:app --port 9002"
Launch "frontend"  "frontend"  "cmd.exe" "/c npm run dev -- --host 127.0.0.1"

Write-Host ""
Write-Host "ChaosButton  http://localhost:5173"
Write-Host "API docs     http://localhost:8000/docs"
Write-Host "Weak shop    http://127.0.0.1:9001   Resilient shop  http://127.0.0.1:9002"
