"""Resilience score model: weights, normalisation and handling of unavailable data."""
from app.metrics.scoring import WEIGHTS, compute_score, latency_component, recovery_component


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_component_normalisation_is_bounded():
    assert recovery_component(0.5) == 100 and recovery_component(30) == 0 and recovery_component(99) == 0
    assert latency_component(50, 50) == 100 and latency_component(500, 50) == 0
    assert latency_component(100, None) is None


def test_perfect_inputs_score_100():
    assert compute_score(100, 100, 0.5, 50, 50)["overall"] == 100


def test_unavailable_components_are_excluded_and_reported():
    score = compute_score(100, None, None, 50, 50)
    assert score["overall"] == 100
    assert not score["components"]["fallback"]["available"]
    assert abs(sum(c["effective_weight"] for c in score["components"].values()) - 1) < 1e-3
    assert len(score["notes"]) == 2


def test_failures_lower_the_score():
    assert compute_score(0, 0, None, 5000, 50)["overall"] == 0
    assert compute_score(None, None, None, None, None)["overall"] is None
