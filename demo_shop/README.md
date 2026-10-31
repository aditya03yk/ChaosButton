# Demo shop

Two versions of the same tiny shop so ChaosButton can be demonstrated without any external app.

| Service | Port | Purpose |
|---|---|---|
| `inventory_service.py` | 9100 | Upstream dependency (inventory + payment) |
| `weak_app.py` | 9001 | No timeouts, no retries, no fallback |
| `resilient_app.py` | 9002 | Finite timeout, bounded retries + backoff, circuit breaker, fallbacks |

Both shops call their dependency through ChaosButton's `/upstream` gateway
(`UPSTREAM_URL`, default `http://127.0.0.1:8000/upstream`). With no experiment running the gateway
forwards traffic untouched; during an experiment it injects faults on the dependency call
(scope **dependency**, dependency route `/inventory`), so the two apps react differently.

Run `scripts/start.sh` (or `start.ps1`) from the repository root.
