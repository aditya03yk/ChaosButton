# ChaosButton

**Break it before your users do.** AI-assisted application resilience testing.

## What is ChaosButton?

Developers usually test the happy path. In production a payment API turns slow, a dependency returns 503, or a
timeout is missing, and the failure surfaces in front of users. ChaosButton is a local-first workbench that closes
that loop:

1. **Connect** an application you own (localhost by default).
2. **Inject** bounded faults (latency, timeout, HTTP 500/503) into matching requests only.
3. **Measure** success/error rate, P50/P95 latency, recovery time and a transparent resilience score, all computed by code.
4. **Explain** the weakness with a local open-weight model (Gemma through Ollama).
5. **Fix**: review a stack-specific code proposal and apply it yourself. ChaosButton never edits your code.
6. **Re-test** the identical experiment and compare before/after.

*Facts come from code, explanations come from AI.* The AI never computes metrics or decides pass/fail.

## Features

- Target management with SSRF protection (loopback by default, allow-list + ownership confirmation for remote hosts).
- **Auto Chaos Test**: latency, timeout and HTTP 503 suite with conservative bounded defaults and a consolidated report.
- **Manual Chaos Test**: choose route, method, fault, intensity, duration, request cap, timeout threshold.
- Fault-injection proxy (FastAPI + httpx) with route scoping, request caps, automatic expiry and a kill switch.
- Live monitoring over SSE: metrics, latency / volume / outcome / status charts, event timeline, auto-reconnect.
- Deterministic metrics and a documented resilience score (40% success, 25% fallback, 20% recovery, 15% latency).
- Gemma analysis: failure explanation, root-cause hypotheses, severity, code fix, schema-validated with one retry.
- Fix workspace (proposed → reviewed → applied → verified, all manual), retest, before/after comparison, history, JSON reports.
- Demo shop with a **weak** and a **resilient** version for a repeatable, genuine demonstration.

## Architecture

```
Developer
   |
React + Vite + Tailwind dashboard  --SSE/REST-->  FastAPI control plane
                                                    | targets | experiments | safety limits | kill switch
                                                    v
                                         Experiment runner (asyncio)
                                                    |
                                         Fault-injection proxy (httpx)
                                       /proxy/{id}/..        /upstream/..
                                                    |
                              Target app  <---------+---------> its dependency (demo: inventory service)
                                                    |
                                         Request events -> Metrics + score engine (deterministic)
                                                    |
                                         Gemma via Ollama (structured JSON, validated)
                                                    |
                                         SQLite report store -> dashboard and reports
```

Two injection points share one rule engine: **inbound** (client → target route) and **dependency** (the target's
own upstream calls, routed through `/upstream`). The demo shops use the dependency point, which is why the weak and
resilient apps genuinely behave differently. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tech Stack

Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLModel/SQLAlchemy, SQLite, httpx, asyncio, pytest ·
React, Vite, TypeScript, Tailwind CSS, React Router, Recharts, Lucide · Ollama + Gemma.

## Prerequisites

Python 3.11+, Node.js 18+, npm, [Ollama](https://ollama.com) and a Gemma model (optional for non-AI features).

## Installation

```bash
# Linux / macOS
scripts/setup.sh
# Windows PowerShell
scripts\setup.ps1
```

This creates `.venv`, installs backend and frontend dependencies, creates `.env` from `.env.example` and initialises
the SQLite database.

## Quick Start

```bash
scripts/start.sh        # or scripts\start.ps1 on Windows
```

| Service | URL |
|---|---|
| ChaosButton (frontend) | http://localhost:5173 |
| Backend + Swagger | http://localhost:8000 · http://localhost:8000/docs |
| Weak demo shop | http://127.0.0.1:9001 |
| Resilient demo shop | http://127.0.0.1:9002 |
| Demo upstream (inventory/payment) | http://127.0.0.1:9100 |

Manual start (from the repo root, with the venv active):

```bash
cd backend && uvicorn app.main:app --port 8000
cd demo_shop && uvicorn inventory_service:app --port 9100
cd demo_shop && uvicorn weak_app:app --port 9001
cd demo_shop && uvicorn resilient_app:app --port 9002
cd frontend && npm run dev
```

## Gemma Setup

```bash
# 1. Install Ollama from https://ollama.com
# 2. Start the service (the desktop app does this automatically)
ollama serve
# 3. Download a Gemma model and test it
ollama pull gemma3:4b
ollama run gemma3:4b
# 4. Use the exact tag from `ollama list` in .env
#    OLLAMA_MODEL=gemma3:4b
```

The dashboard top bar and **Settings** show whether Ollama is reachable and the model is installed. Without Ollama,
the AI panel shows an honest error with a retry button; every non-AI feature keeps working and nothing is faked.

## Usage

**Auto Chaos Test**: Targets → *Add demo shops* → Auto Chaos Test → *Use demo shop preset* → Start. Latency (500 ms),
timeout (2000 ms) and HTTP 503 run in sequence, each with baseline → fault → recovery.

**Manual Chaos Test**: pick a target, route, method, fault, duration and request cap. The exact scope and limits are
shown before the run starts. *Stop now* is the kill switch.

### Demo walkthrough

1. Add the demo shops; select **Demo shop (weak)**; run the Auto Chaos Test with the preset.
2. Watch latency, errors and the timeline update live; open a scenario's results (timeouts and 503s become HTTP 500s).
3. *Analyse with Gemma*: diagnosis, severity, and a timeout/fallback fix proposal.
4. Review the fix in the **Fix workspace** (mark reviewed/applied manually).
5. On the Results page choose **Demo shop (resilient)** under *Retest* and rerun the same experiment.
6. Open **Compare runs** (or the report) to see the measured before/after difference and optional Gemma reading.

## Safety

Loopback-only by default; remote targets need ownership confirmation **and** an `ALLOWED_REMOTE_HOSTS` entry **and**
public-only addresses. Hard backend limits on duration, affected requests, delay, concurrency and baseline size. One
experiment at a time. Faults expire server-side and a kill switch clears them immediately. Sensitive headers are
redacted and request bodies are never stored. AI output is a proposal only. Details: [docs/SAFETY.md](docs/SAFETY.md).

## Project Structure

```
backend/app/   core (config, security, logging) · api · engine (runner, orchestrator, event bus) ·
               proxy (gateway, rules, injector) · metrics · ai · models · storage · services
backend/tests/ pytest suite
frontend/src/  pages · components · hooks · services · types
demo_shop/     weak + resilient shops and the upstream service
scripts/       setup and start scripts (sh + ps1)
docs/          ARCHITECTURE, API, SAFETY, AI
```

## API Documentation

Swagger UI: http://localhost:8000/docs (OpenAPI JSON at `/openapi.json`). Summary in [docs/API.md](docs/API.md).

## Testing

```bash
cd backend && pytest          # backend unit + API + integration tests
cd frontend && npm test       # component tests (vitest)
```

The suite needs no internet and no running Gemma; the AI provider is mocked at the test boundary only.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Ollama is not reachable" | Run `ollama serve`, then press retry |
| "Model … is not installed" | `ollama pull <model>` and match `OLLAMA_MODEL` to `ollama list` |
| Target validation: "not reachable" | Start the app; for the demo shops run `scripts/start.sh` |
| Demo shop errors outside experiments | The backend must be running (shops call `/upstream`), or set `UPSTREAM_URL=http://127.0.0.1:9100` |
| "Another experiment is already running" | Stop it from the live monitor |
| Experiment `FAILED: Baseline failed` | The target returned no successful responses before any fault |
| Gemma returns invalid output | Retry; try a larger model tag; raise `OLLAMA_TIMEOUT` |

## AI Tools Used

- **Claude (Anthropic)** assisted with generating and reviewing the code in this repository. Every contributor must be
  able to explain every module.
- **Gemma (Google, open weights) via Ollama** runs inside the application to explain results and propose fixes.

## Credits

FastAPI, Uvicorn, Pydantic, SQLModel, SQLAlchemy, SQLite, httpx, pytest, React, Vite, TypeScript, Tailwind CSS,
React Router, Recharts, Lucide, Vitest, Testing Library, Ollama, Gemma (Google).

## Licence

MIT, see [LICENSE](LICENSE).
