# Safety

| Control | Enforcement |
|---|---|
| Loopback by default | `core/security.py` resolves the host and requires loopback addresses |
| Remote targets | Ownership confirmation + non-local environment + `ALLOWED_REMOTE_HOSTS` + public-only addresses (private, link-local, reserved rejected) |
| SSRF / redirects | Credentials in URLs rejected; the proxy never follows redirects; targets pointing at ChaosButton itself rejected; `/proxy` only serves registered targets |
| Hard limits | `ExperimentCreate` validator rejects values above `MAX_*` settings; the frontend cannot override them |
| Route scope | Exact routes or `/prefix/*`; `/` and `/*` are rejected |
| One run at a time | Orchestrator rejects a second start (409) |
| Automatic expiry | Each rule has `expires_at`, checked on every lookup, independent of the browser |
| Kill switch | `POST /stop` clears the rule first, cancels the task, persists `STOPPED`; the runner also clears rules in `finally` |
| Data protection | Authorization/cookie headers redacted in logs; request bodies never stored; `.env` git-ignored |
| Human approval | AI output is a proposal; no code is edited, committed, deployed or executed |

## Known limits

DNS is validated at registration and again before every run, but connections are not pinned to the validated IP, so a
hostile DNS server could still rebind between validation and connection. Remote targets should be used with care.
Never point ChaosButton at production or customer-facing systems.
