"""Deterministic metric calculations. The AI layer never computes these numbers."""
from datetime import datetime
from typing import Iterable, Optional, Sequence

from app.metrics.recovery import measure_recovery
from app.metrics.scoring import compute_score


def percentile(values: Sequence[float], pct: float) -> Optional[float]:
    """Linear-interpolated percentile (pct in 0-100). None for an empty sample."""
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct / 100
    low, high = int(rank), min(int(rank) + 1, len(ordered) - 1)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (rank - low), 2)


def _rate(part: int, total: int) -> Optional[float]:
    return round(part / total * 100, 2) if total else None


def summarize(events: Sequence) -> dict:
    """Aggregate request events. A request is a success only if it is not timed out and
    its status is below 400; every other request counts as exactly one failure."""
    total = len(events)
    successful = sum(1 for e in events if e.success)
    latencies = [e.latency_ms for e in events]
    return {
        "total": total,
        "successful": successful,
        "failed": total - successful,
        "timeouts": sum(1 for e in events if e.timed_out),
        "fallbacks": sum(1 for e in events if getattr(e, "fallback_used", False)),
        "success_rate": _rate(successful, total),
        "error_rate": _rate(total - successful, total),
        "average_latency": round(sum(latencies) / total, 2) if total else None,
        "p50_latency": percentile(latencies, 50),
        "p95_latency": percentile(latencies, 95),
    }


def fallback_score(stats: dict) -> Optional[float]:
    """Share of degraded requests (failed or served by fallback) that were served by a fallback.
    Unavailable when nothing degraded, because there was nothing to fall back from."""
    degraded = stats["failed"] + stats["fallbacks"]
    return _rate(stats["fallbacks"], degraded) if degraded else None


def status_distribution(events: Iterable) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        key = "timeout" if event.timed_out else str(event.status_code or "error")
        counts[key] = counts.get(key, 0) + 1
    return counts


def live_snapshot(fault_events: Sequence, *, active_faults: int, started_at: Optional[datetime],
                  now: datetime, phase: str) -> dict:
    """Authoritative live metrics streamed to the dashboard."""
    stats = summarize(fault_events)
    return {**stats, "status_counts": status_distribution(fault_events), "active_faults": active_faults,
            "phase": phase, "duration_s": round((now - started_at).total_seconds(), 1) if started_at else 0}


def build_experiment_metrics(events: Sequence, fault_removed_at: Optional[datetime]) -> Optional[dict]:
    """Compute all persisted metrics from a run's events. None when no fault-period data exists."""
    by_phase = {p: [e for e in events if e.phase == p] for p in ("baseline", "fault", "recovery")}
    fault = summarize(by_phase["fault"])
    if not fault["total"]:
        return None
    baseline = summarize(by_phase["baseline"])
    recovery = measure_recovery(by_phase["recovery"], baseline["p95_latency"], fault_removed_at)
    fb = fallback_score(fault)
    score = compute_score(fault["success_rate"], fb, recovery, fault["p95_latency"], baseline["p95_latency"])
    limitations = list(score["notes"])
    if fault["total"] < 20:
        limitations.append(f"Small sample ({fault['total']} fault-period requests): results are indicative only.")
    return {
        "total_requests": fault["total"], "successful_requests": fault["successful"],
        "failed_requests": fault["failed"], "timeout_count": fault["timeouts"],
        "success_rate": fault["success_rate"], "error_rate": fault["error_rate"],
        "p50_latency": fault["p50_latency"], "p95_latency": fault["p95_latency"],
        "average_latency": fault["average_latency"], "fallback_score": fb, "recovery_time": recovery,
        "resilience_score": score["overall"], "baseline_requests": baseline["total"],
        "baseline_p50_latency": baseline["p50_latency"], "baseline_p95_latency": baseline["p95_latency"],
        "sample_size": len(events), "score_components": score["components"], "limitations": limitations,
    }
