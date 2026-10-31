"""Before/after comparison of two experiment runs using stored values only."""
from typing import Any, Optional

# metric -> True when a higher value is better
METRICS = {"success_rate": True, "error_rate": False, "p50_latency": False, "p95_latency": False,
           "recovery_time": False, "fallback_score": True, "resilience_score": True}
CONFIG_KEYS = ("scope", "dependency_route", "delay_ms", "timeout_ms", "duration_s", "max_affected",
               "baseline_requests", "request_timeout_ms", "concurrency", "interval_ms")
EPSILON = 0.01


def incompatibilities(a: Any, b: Any) -> list[str]:
    """Reasons two experiments are not a controlled before/after pair (empty = comparable).
    A different target is allowed (e.g. weak vs resilient app) and reported separately."""
    reasons = []
    for attr in ("fault_type", "route", "method"):
        if getattr(a, attr) != getattr(b, attr):
            reasons.append(f"{attr} differs ({getattr(a, attr)} vs {getattr(b, attr)})")
    for key in CONFIG_KEYS:
        if a.fault_configuration.get(key) != b.fault_configuration.get(key):
            reasons.append(f"fault parameter '{key}' differs")
    return reasons


def _delta(name: str, before: Optional[float], after: Optional[float]) -> dict:
    row = {"metric": name, "original": before, "retest": after, "absolute_diff": None,
           "percent_diff": None, "verdict": "unavailable"}
    if before is None or after is None:
        return row
    diff = round(after - before, 2)
    row["absolute_diff"] = diff
    row["percent_diff"] = round(diff / before * 100, 1) if before else None
    if abs(diff) < EPSILON:
        row["verdict"] = "unchanged"
    else:
        row["verdict"] = "improved" if (diff > 0) == METRICS[name] else "regressed"
    return row


def compare(exp_a: Any, metrics_a: Any, exp_b: Any, metrics_b: Any) -> dict:
    reasons = incompatibilities(exp_a, exp_b)
    rows = [_delta(name, getattr(metrics_a, name), getattr(metrics_b, name)) for name in METRICS]
    verdicts = [r["verdict"] for r in rows]
    return {"comparable": not reasons, "incompatibilities": reasons,
            "target_changed": exp_a.target_id != exp_b.target_id,
            "original_id": exp_a.id, "retest_id": exp_b.id, "rows": rows,
            "improved": verdicts.count("improved"), "regressed": verdicts.count("regressed")}
