#!/usr/bin/env bash
# Starts the local demo services, backend and frontend. Ctrl+C stops everything.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
PY="$PWD/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Python environment missing. Run: bash scripts/setup.sh" >&2
  exit 1
fi
if [[ ! -d frontend/node_modules ]]; then
  echo "Frontend dependencies missing. Run: bash scripts/setup.sh" >&2
  exit 1
fi
mkdir -p .run
pids=()

cleanup() {
  local code=$?
  trap - INT TERM EXIT
  for pid in "${pids[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  for pid in "${pids[@]:-}"; do wait "$pid" 2>/dev/null || true; done
  exit "$code"
}
trap cleanup INT TERM EXIT

launch() {
  local name=$1 dir=$2; shift 2
  (cd "$dir" && exec "$@") >".run/$name.log" 2>&1 &
  pids+=("$!")
}

wait_for() {
  local name=$1 url=$2
  for _ in $(seq 1 60); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "  OK    $name  $url"
      return 0
    fi
    sleep 0.5
  done
  echo "  ERROR $name did not become ready: $url" >&2
  echo "  --- .run/$name.log ---" >&2
  cat ".run/$name.log" >&2 || true
  return 1
}

# Ollama is optional. Start its local daemon if installed but not already responding.
if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && command -v ollama >/dev/null 2>&1; then
  echo "Starting local Ollama service..."
  ollama serve >.run/ollama.log 2>&1 &
  pids+=("$!")
  for _ in $(seq 1 20); do
    curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
    sleep 0.5
  done
fi

launch inventory demo_shop "$PY" -m uvicorn inventory_service:app --host 127.0.0.1 --port 9100
launch backend backend "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
launch weak demo_shop "$PY" -m uvicorn weak_app:app --host 127.0.0.1 --port 9001
launch resilient demo_shop "$PY" -m uvicorn resilient_app:app --host 127.0.0.1 --port 9002
launch frontend frontend npm run dev -- --host 127.0.0.1 --port 5173

echo "Starting ChaosButton services..."
wait_for inventory http://127.0.0.1:9100/health
wait_for backend http://127.0.0.1:8000/health
wait_for weak http://127.0.0.1:9001/health
wait_for resilient http://127.0.0.1:9002/health
wait_for frontend http://127.0.0.1:5173

echo
echo "ChaosButton  http://localhost:5173"
echo "API docs     http://localhost:8000/docs"
echo "Weak shop    http://127.0.0.1:9001"
echo "Resilient    http://127.0.0.1:9002"
echo "Inventory    http://127.0.0.1:9100"
if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama       http://127.0.0.1:11434 (reachable; model availability shown in Settings)"
else
  echo "Ollama       offline (AI disabled; install/start Ollama and pull the configured model)"
fi
echo "Press Ctrl+C to stop all started services."
wait
