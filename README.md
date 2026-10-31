# ChaosButton

**Break it before your users do.**

AI-assisted application resilience testing.

## What is ChaosButton?

Developers usually test the happy path. But in production, a payment API becomes slow, a dependency returns HTTP 503, or a missing timeout causes failures that directly affect users.

ChaosButton is a local-first workbench designed to help developers identify and understand application weaknesses through controlled fault injection and resilience testing.

Its workflow:

1. **Connect:** Register an application you own (localhost is allowed by default).
2. **Inject:** Introduce bounded faults such as latency, timeouts, and HTTP 500/503 errors into matching requests.
3. **Measure:** Track success rate, error rate, P50/P95 latency, recovery time, and a transparent resilience score.
4. **Explain:** Use a local open-weight model (Gemma through Ollama) to analyze failures.
5. **Fix:** Review stack-specific code suggestions and apply changes manually. ChaosButton never edits your application code.
6. **Re-test:** Run the same experiment again and compare before-and-after results.

**Facts come from code; explanations come from AI.**

The AI does not calculate metrics or determine experiment pass/fail results.

## Features

- **Target Management:** Register applications with SSRF protection, loopback defaults, remote-host allow-listing, and ownership confirmation.
- **Auto Chaos Test:** Run latency, timeout, and HTTP 503 scenarios with bounded defaults and consolidated reports.
- **Manual Chaos Test:** Select routes, HTTP methods, fault types, intensity, duration, request limits, and timeout thresholds.
- **Fault Injection Proxy:** FastAPI and httpx-based proxy with route scoping, request caps, automatic fault expiry, and a kill switch.
- **Live Monitoring:** Server-Sent Events (SSE) for live metrics, latency, request volume, outcomes, status charts, and event timelines.
- **Resilience Metrics:** Deterministic metrics and a documented resilience score:
  - 40% Success rate
  - 25% Fallback performance
  - 20% Recovery
  - 15% Latency
- **Gemma AI Analysis:** Failure explanations, root-cause hypotheses, severity assessment, and code-fix proposals with schema validation and retry handling.
- **Fix Workspace:** Track proposed, reviewed, applied, and verified fixes manually.
- **Experiment Comparison:** Compare before-and-after experiment results.
- **Reports:** Experiment history and JSON reports.
- **Demo Shop:** Includes weak and resilient demo applications for repeatable demonstrations.

## Architecture

```text
Developer
   |
   v
React + Vite + Tailwind Dashboard
   |
   | REST API / SSE
   v
FastAPI Control Plane
   |
   | Targets | Experiments | Safety Limits | Kill Switch
   v
Experiment Runner (asyncio)
   |
   v
Fault Injection Proxy (httpx)
   |
   +--------------------+
   |                    |
   v                    v
Target Application   Dependency Service
   |                    |
   +--------------------+
            |
            v
     Request Events
            |
            v
  Metrics + Score Engine
      (Deterministic)
            |
            v
     Gemma via Ollama
   (Structured JSON Output)
            |
            v
      SQLite Report Store
            |
            v
      Dashboard / Reports
```

Two injection points share the same rule engine:

- **Inbound injection:** Client-to-target application routes.
- **Dependency injection:** The target application's own upstream calls, routed through `/upstream`.

The demo shops use the dependency injection point, allowing the weak and resilient applications to demonstrate different failure-handling behaviours.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for more details.

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- SQLModel / SQLAlchemy
- SQLite
- httpx
- asyncio
- pytest

### Frontend
- React
- Vite
- TypeScript
- Tailwind CSS
- React Router
- Recharts
- Lucide
- Vitest
- Testing Library

### AI
- Ollama
- Gemma (Google open-weight model)

## Prerequisites

Install the following before setting up ChaosButton:

- Python 3.11 or newer
- Node.js 18 or newer
- npm
- Git
- Ollama (optional, required for local Gemma AI analysis)

Download Ollama from [https://ollama.com](https://ollama.com).

## Installation

Clone the repository:

```bash
git clone https://github.com/aditya03yk/ChaosButton.git
cd ChaosButton
```

### macOS / Linux

Run:

```bash
bash scripts/setup.sh
```

### Windows PowerShell

Run:

```powershell
.\scripts\setup.ps1
```

The setup script prepares the Python virtual environment, installs backend and frontend dependencies, creates `.env` from `.env.example` if needed, and initializes the SQLite database.

## Quick Start

After completing installation, start ChaosButton.

### macOS / Linux

```bash
bash scripts/start.sh
```

### Windows PowerShell

```powershell
.\scripts\start.ps1
```

Keep the terminal running while using the application.

## Application URLs

| Service | URL |
|---|---|
| ChaosButton Dashboard | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger API Documentation | http://localhost:8000/docs |
| Weak Demo Shop | http://127.0.0.1:9001 |
| Resilient Demo Shop | http://127.0.0.1:9002 |
| Demo Inventory Service | http://127.0.0.1:9100 |

## Manual Startup

If you prefer to start individual services, activate the virtual environment first.

Start each service in a separate terminal.

**Terminal 1 — Backend**

```bash
cd backend
uvicorn app.main:app --port 8000
```

**Terminal 2 — Inventory Service**

```bash
cd demo_shop
uvicorn inventory_service:app --port 9100
```

**Terminal 3 — Weak Demo Shop**

```bash
cd demo_shop
uvicorn weak_app:app --port 9001
```

**Terminal 4 — Resilient Demo Shop**

```bash
cd demo_shop
uvicorn resilient_app:app --port 9002
```

**Terminal 5 — Frontend**

```bash
cd frontend
npm run dev
```

## Gemma Setup

ChaosButton uses Ollama to run Gemma locally for AI-powered experiment analysis.

### 1. Install Ollama

Download and install Ollama:

[https://ollama.com](https://ollama.com)

### 2. Start Ollama

```bash
ollama serve
```

The Ollama desktop application may start the service automatically.

### 3. Download Gemma

```bash
ollama pull gemma3:4b
```

### 4. Test the model

```bash
ollama run gemma3:4b
```

### 5. Configure the model

Check the installed model tag:

```bash
ollama list
```

Make sure your `.env` configuration uses the matching model name:

```env
OLLAMA_MODEL=gemma3:4b
```

The dashboard and Settings page indicate whether Ollama is reachable and whether the configured model is installed.

Without Ollama, non-AI features remain available. AI analysis reports an error rather than displaying fabricated results.

## Usage

### 1. Add a Target

- Open the Targets page.
- Click **Add demo shops** to register the two built-in demo applications.
- Alternatively, register an application you own using its name and base URL.
- Validate the target before testing.

### 2. Run Auto Chaos Test

- Navigate to **Auto Chaos Test**.
- Select a demo target.
- Choose **Use demo shop preset**.
- Start the experiment.
- Observe the baseline, fault-injection, and recovery stages.

The demo preset uses latency, timeout, and HTTP 503 scenarios.

### 3. Run Manual Chaos Test

- Open **Manual Chaos Test**.
- Select a target.
- Choose the route and HTTP method.
- Select the fault type.
- Configure duration, intensity, and request limits.
- Review the experiment scope before starting.
- Use **Stop now** if you need to terminate the experiment.

### 4. Analyse Results with Gemma

After an experiment:

- Open the experiment results.
- Select **Analyse with Gemma**.
- Review the failure explanation.
- Examine root-cause hypotheses and severity.
- Review the suggested code fix.

AI-generated suggestions are proposals and must be reviewed and applied manually.

### 5. Review Fixes

Use the Fix Workspace to track fixes through:

- Proposed
- Reviewed
- Applied
- Verified

ChaosButton does not directly modify your target application's source code.

### 6. Compare Experiments

Run the same experiment against the resilient demo shop.

Open the comparison or report view to examine measured differences in performance and failure handling.

## Demo Walkthrough

A simple demonstration of ChaosButton:

1. Register both demo shops using **Add demo shops**.
2. Select **Demo shop (weak)**.
3. Run Auto Chaos Test using the demo preset.
4. Observe latency, errors, and the live event timeline.
5. Analyse the results using Gemma.
6. Review the