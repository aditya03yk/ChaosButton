"""Transparent resilience score.

Weights: 40% request success, 25% fallback behaviour, 20% recovery time, 15% latency impact.
Each component is normalised to 0-100:
  - success:  fault-period success rate (%).
  - fallback: share of degraded requests served by a fallback (%).
  - recovery: 100 at <= 1 s, 0 at >= 30 s, linear between.
  - latency:  ratio = fault p95 / baseline p95; 100 at ratio <= 1, 0 at ratio >= 10, linear between.
Unavailable components are excluded and the remaining weights are re-normalised; this is reported
in `notes` so missing data is never silently treated as perfect.
The score is a comparative indicator, not a reliability certification.
"""
from typing import Optional

WEIGHTS = {"request_success": 0.40, "fallback": 0.25, "recovery": 0.20, "latency": 0.15}
RECOVERY_BEST_S, RECOVERY_WORST_S = 1.0, 30.0
LATENCY_BEST_RATIO, LATENCY_WORST_RATIO = 1.0, 10.0


def _clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def recovery_component(recovery_s: Optional[float]) -> Optional[float]:
    if recovery_s is None:
        return None
    span = RECOVERY_WORST_S - RECOVERY_BEST_S
    return _clamp(100 * (RECOVERY_WORST_S - recovery_s) / span)


def latency_component(fault_p95: Optional[float], baseline_p95: Optional[float]) -> Optional[float]:
    if fault_p95 is None or not baseline_p95:
        return None
    ratio = fault_p95 / baseline_p95
    span = LATENCY_WORST_RATIO - LATENCY_BEST_RATIO
    return _clamp(100 * (LATENCY_WORST_RATIO - ratio) / span)


def compute_score(success_rate: Optional[float], fallback: Optional[float], recovery_s: Optional[float],
                  fault_p95: Optional[float], baseline_p95: Optional[float]) -> dict:
    values = {
        "request_success": None if success_rate is None else _clamp(success_rate),
        "fallback": None if fallback is None else _clamp(fallback),
        "recovery": recovery_component(recovery_s),
        "latency": latency_component(fault_p95, baseline_p95),
    }
    available = {k: v for k, v in values.items() if v is not None}
    total_weight = sum(WEIGHTS[k] for k in available)
    overall = _clamp(sum(v * WEIGHTS[k] for k, v in available.items()) / total_weight) if available else None
    components = {k: {"value": values[k], "weight": WEIGHTS[k], "available": values[k] is not None,
                      "effective_weight": round(WEIGHTS[k] / total_weight, 4) if k in available else 0.0}
                  for k in WEIGHTS}
    notes = [f"'{k.replace('_', ' ')}' was unavailable and excluded; remaining weights were re-normalised."
             for k, v in values.items() if v is None]
    return {"overall": overall, "components": components, "notes": notes}
