#!/usr/bin/env bash
# ChaosButton setup: Python venv, backend + frontend dependencies, database, Ollama check.
set -euo pipefail
cd "$(dirname "$0")/.."

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required tool: $1"; exit 1; }; }
need python3; need node; need npm; need curl
python3 - <<'PYVER'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required; found " + sys.version.split()[0])
print("Python", sys.version.split()[0])
PYVER
node -e 'const major = Number(process.versions.node.split(".")[0]); if (major < 18) { console.error("Node.js 18 or newer is required"); process.exit(1); } console.log("Node.js", process.version);'

python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt -r demo_shop/requirements.txt
(cd frontend && npm install)
[ -f .env ] || cp .env.example .env

(cd backend && ../.venv/bin/python -c "from app.core.config import get_settings; from app.storage import database; database.configure(get_settings().database_url); print('Database initialised')")

if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama is running."
else
  echo "Ollama is not running. Install it from https://ollama.com, then:"
  echo "  ollama serve        # if it is not already running"
  echo "  ollama pull gemma3:4b"
  echo "AI features stay disabled until then; everything else works."
fi
echo "Setup complete. Start everything with: scripts/start.sh"
