# Architecture

## Request flow

The runner sends measured requests through `ProxyGateway`. The gateway asks the `RuleRegistry` for an active rule
matching scope, target, method, route and request cap, applies the fault (`fault_injector`) or forwards via httpx.

## Injection points

| Scope | Where the fault is applied | Used for |
|---|---|---|
| `inbound` | Client → target route (`/proxy/{target_id}/...` or the runner's in-process gateway) | Any HTTP target |
| `dependency` | Target → upstream (`/upstream/...`, forwarded to `UPSTREAM_URL`) | Demo shops; apps that call dependencies through ChaosButton |

The request cap counts **distinct client requests** (via `X-Chaos-Request-Id`), so retries of an affected request stay
affected and apps that retry are not given an unfairly smaller fault exposure.

## Experiment lifecycle

`CREATED → VALIDATING → BASELINE → RUNNING → RECOVERING → COMPLETED`, with `STOPPED` (kill switch) and `FAILED` reachable
from any active state. Transitions are enforced in `engine/state_manager.py`. Only one experiment runs at a time.

## Modules

| Module | Responsibility |
|---|---|
| `api/` | HTTP routes only |
| `services/` | Target, experiment and report logic |
| `storage/` | SQLite engine and repositories |
| `engine/` | Runner, orchestrator (start/stop/suites), event bus (SSE), state machine |
| `proxy/` | Gateway, rules, injector, route matcher |
| `metrics/` | Calculator, recovery, scoring, comparison (pure Python) |
| `ai/` | Provider interface, Ollama/Gemma provider, prompts, schemas, service |

## Metric definitions

- **Success**: not timed out and status < 400 (fallback responses with 2xx count as success). Everything else is exactly one failure.
- **Percentiles**: linear interpolation over fault-period latencies.
- **Recovery**: 3 consecutive normal probes (success, no fallback, latency ≤ max(1.5 × baseline p95, baseline p95 + 100 ms)); time from fault removal to the first of them. `unavailable` if never observed.
- **Fallback score**: fallback responses ÷ (fallback responses + failures). `unavailable` when nothing degraded.
- **Resilience score**: see `metrics/scoring.py`; unavailable components are excluded and weights re-normalised, and this is reported.

## Persistence

Targets, experiments, request events, timeline events, metrics, AI analyses and fix records are stored in SQLite.
Events are bounded by the request caps. After a restart, non-terminal experiments are marked `FAILED`.
