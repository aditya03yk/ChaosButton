#!/usr/bin/env bash
# Diagnose local ChaosButton prerequisites and service availability.
set -u
cd "$(dirname "$0")/.."
failed=0
check_cmd() {
  local cmd=$1 label=$2
  if command -v "$cmd" >/dev/null 2>&1; then printf 'OK      %s: %s\n' "$label" "$(command -v "$cmd")"; else printf 'MISSING %s: install %s\n' "$label" "$cmd"; failed=1; fi
}
check_url() {
  local label=$1 url=$2
  if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then printf 'ONLINE  %s (%s)\n' "$label" "$url"; else printf 'OFFLINE %s (%s)\n' "$label" "$url"; fi
}
check_cmd python3 Python
check_cmd node Node.js
check_cmd npm npm
if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
import sys
print(f"INFO    Python version: {sys.version.split()[0]}")
if sys.version_info < (3, 11):
    print("ERROR   Python 3.11 or newer is required")
    raise SystemExit(1)
PY
  [[ $? -eq 0 ]] || failed=1
fi
if [[ -x .venv/bin/python ]]; then echo "OK      Python virtual environment exists"; else echo "MISSING .venv; run bash scripts/setup.sh"; failed=1; fi
if [[ -d frontend/node_modules ]]; then echo "OK      Frontend dependencies installed"; else echo "MISSING frontend/node_modules; run bash scripts/setup.sh"; failed=1; fi
check_url "Backend API" http://127.0.0.1:8000/health
check_url "Inventory demo" http://127.0.0.1:9100/health
check_url "Weak demo shop" http://127.0.0.1:9001/health
check_url "Resilient demo shop" http://127.0.0.1:9002/health
check_url "Frontend" http://127.0.0.1:5173
if curl -fsS --max-time 2 http://127.0.0.1:11434/api/tags >/tmp/chaosbutton-ollama-tags.json 2>/dev/null; then
  echo "ONLINE  Ollama API"
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import json, os
try:
    data=json.load(open('/tmp/chaosbutton-ollama-tags.json'))
    names=[m.get('name','') for m in data.get('models',[]) if isinstance(m,dict)]
    wanted=os.environ.get('OLLAMA_MODEL','gemma3:4b')
    print('INFO    Installed Ollama models: '+(', '.join(names) if names else '(none)'))
    if wanted not in names and wanted+':latest' not in names:
        print(f'NEEDS   Pull configured model: ollama pull {wanted}')
except Exception as exc:
    print(f'WARN    Could not parse Ollama model list: {exc}')
PY
  fi
else
  echo "OFFLINE Ollama API; AI features unavailable until Ollama is started"
  command -v ollama >/dev/null 2>&1 && echo "HINT    Start it with: ollama serve" || echo "HINT    Install Ollama from https://ollama.com"
fi
[[ -d .run ]] && echo "INFO    Runtime logs: .run/*.log"
exit "$failed"
