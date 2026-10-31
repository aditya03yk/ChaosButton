"""Metric calculations: percentiles, rates, fallback, recovery and comparison."""
from datetime import datetime, timedelta
from types import SimpleNamespace as NS

from app.metrics.calculator import build_experiment_metrics, fallback_score, percentile, summarize
from app.metrics.comparison import compare, incompatibilities
from app.metrics.recovery import measure_recovery

T0 = datetime(2026, 1, 1)


def ev(phase="fault", sec=0, latency=100.0, ok=True, timed_out=False, fallback=False):
    return NS(phase=phase, timestamp=T0 + timedelta(seconds=sec), latency_ms=latency, success=ok,
              timed_out=timed_out, fallback_used=fallback, status_code=200 if ok else 503)


def test_percentiles():
    assert percentile([], 50) is None
    assert percentile([10, 20, 30, 40, 50], 50) == 30
    assert percentile([100, 200, 300, 400], 95) == 385.0


def test_rates_do_not_double_count():
    stats = summarize([ev(), ev(ok=False), ev(ok=False, timed_out=True), ev()])
    assert (stats["total"], stats["successful"], stats["failed"], stats["timeouts"]) == (4, 2, 2, 1)
    assert stats["success_rate"] + stats["error_rate"] == 100


def test_fallback_score_unavailable_without_degradation():
    assert fallback_score(summarize([ev(), ev()])) is None
    assert fallback_score(summarize([ev(fallback=True), ev(ok=False)])) == 50.0


def test_recovery_requires_streak_of_normal_probes():
    probes = [ev("recovery", 1, 900), ev("recovery", 2, 50), ev("recovery", 3, 50), ev("recovery", 4, 50)]
    assert measure_recovery(probes, 50, T0) == 2.0
    assert measure_recovery(probes[:2], 50, T0) is None
    assert measure_recovery([ev("recovery", i, 50, fallback=True) for i in range(5)], 50, T0) is None


def test_build_metrics_uses_fault_phase_only():
    events = [ev("baseline", i, 50) for i in range(4)] + [ev("fault", 10 + i, 500, ok=i % 2 == 0) for i in range(10)]
    events += [ev("recovery", 20 + i, 50) for i in range(4)]
    m = build_experiment_metrics(events, T0 + timedelta(seconds=19))
    assert m["total_requests"] == 10 and m["success_rate"] == 50.0 and m["baseline_p95_latency"] == 50.0
    assert m["recovery_time"] == 1.0 and m["sample_size"] == 18
    assert build_experiment_metrics([ev("baseline")], None) is None


def test_comparison_verdicts_and_compatibility():
    a = NS(id="a", target_id=1, fault_type="latency", route="/p", method="GET", fault_configuration={"delay_ms": 500})
    b = NS(id="b", target_id=2, fault_type="latency", route="/p", method="GET", fault_configuration={"delay_ms": 500})
    ma = NS(success_rate=50, error_rate=50, p50_latency=500, p95_latency=900, recovery_time=None,
            fallback_score=0, resilience_score=30)
    mb = NS(success_rate=100, error_rate=0, p50_latency=100, p95_latency=300, recovery_time=1,
            fallback_score=100, resilience_score=90)
    result = compare(a, ma, b, mb)
    rows = {r["metric"]: r for r in result["rows"]}
    assert result["comparable"] and result["target_changed"]
    assert rows["error_rate"]["verdict"] == "improved" and rows["success_rate"]["verdict"] == "improved"
    assert rows["recovery_time"]["verdict"] == "unavailable"
    b.fault_configuration = {"delay_ms": 900}
    assert incompatibilities(a, b) == ["fault parameter 'delay_ms' differs"]
