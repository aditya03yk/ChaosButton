# API

Interactive docs: `http://localhost:8000/docs`. Errors use `{"detail": "...", "code": "..."}`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/api/system/status` · `/ai-status` · `/config` | Backend, DB and Ollama status; safe config |
| POST | `/api/targets/validate` | Validate a URL (safety + health probe) |
| POST/GET | `/api/targets` | Create / list targets |
| GET/PATCH/DELETE | `/api/targets/{id}` | Read / update / remove |
| POST | `/api/targets/{id}/validate` | Revalidate a stored target |
| POST/GET | `/api/experiments` | Create / list (filters: `target_id`, `fault_type`, `status`, `search`, paging) |
| GET | `/api/experiments/{id}` | Status + metrics summary |
| POST | `/api/experiments/{id}/start` · `/stop` | Start / kill switch |
| GET | `/api/experiments/{id}/events` | Stored request + timeline events |
| GET | `/api/experiments/{id}/stream` | SSE: `status`, `request`, `metrics`, `timeline`, `proxy` |
| GET | `/api/experiments/{id}/report` | Full report (`?download=true` for a JSON file) |
| POST | `/api/experiments/{id}/ai-analysis` | Gemma analysis → proposal + fix record |
| POST | `/api/experiments/{id}/compare` | Before/after (`other_experiment_id`, `explain`) |
| POST | `/api/experiments/{id}/retest` | Clone config as a new run (optional `target_id`) |
| GET | `/api/experiments/{id}/fixes` · PATCH `/api/fixes/{fix_id}` | Fix workspace |
| POST/GET | `/api/suites` · `/api/suites/{id}` · POST `/api/suites/{id}/stop` | Auto Chaos Test suite |
| GET | `/api/dashboard` | Dashboard aggregates |
| ANY | `/proxy/{target_id}/{path}` · `/upstream/{path}` | Fault-injection proxy entry points |
