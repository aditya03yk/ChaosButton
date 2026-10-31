"""Recovery-time measurement.

Recovered = RECOVERY_STREAK consecutive probes that succeed, are not served by a fallback
and are within the normal latency band (max(1.5 x baseline p95, baseline p95 + 100 ms);
1000 ms when no baseline exists). Recovery time is the delay between fault removal and the
start of the first probe of that streak. Returns None if never observed.
"""
from datetime import datetime
from typing import Optional, Sequence

RECOVERY_STREAK = 3
DEFAULT_NORMAL_LATENCY_MS = 1000.0


def normal_latency_ms(baseline_p95: Optional[float]) -> float:
    if baseline_p95 is None:
        return DEFAULT_NORMAL_LATENCY_MS
    return max(baseline_p95 * 1.5, baseline_p95 + 100)


def measure_recovery(probes: Sequence, baseline_p95: Optional[float],
                     fault_removed_at: Optional[datetime]) -> Optional[float]:
    if fault_removed_at is None or len(probes) < RECOVERY_STREAK:
        return None
    limit = normal_latency_ms(baseline_p95)
    streak: list = []
    for probe in sorted(probes, key=lambda p: p.timestamp):
        is_normal = probe.success and not getattr(probe, "fallback_used", False) and probe.latency_ms <= limit
        streak = streak + [probe] if is_normal else []
        if len(streak) == RECOVERY_STREAK:
            return round(max((streak[0].timestamp - fault_removed_at).total_seconds(), 0.0), 2)
    return None
