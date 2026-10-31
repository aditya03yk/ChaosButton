"""Fault injection behaviour, request caps and expiry."""
import asyncio
import time

from app.proxy.fault_injector import apply_fault
from app.proxy.rules import FaultRule, RuleRegistry


def rule(fault_type="latency", **kw):
    defaults = dict(experiment_id="e1", target_id=1, scope="inbound", route="/product", method="GET",
                    fault_type=fault_type, max_affected=2, expires_at=time.time() + 30)
    return FaultRule(**{**defaults, **kw})


def find(reg, request_id, path="/product", method="GET", target_id=1):
    return reg.find(scope="inbound", target_id=target_id, method=method, path=path, request_id=request_id)


def test_latency_delays_then_forwards():
    started = time.perf_counter()
    assert asyncio.run(apply_fault(rule(delay_ms=80))) is None
    assert time.perf_counter() - started >= 0.07


def test_timeout_returns_504_marked_timed_out():
    response = asyncio.run(apply_fault(rule("timeout", timeout_ms=30)))
    assert response.status_code == 504 and response.timed_out


def test_http_error_faults():
    assert asyncio.run(apply_fault(rule("http_503"))).status_code == 503
    assert asyncio.run(apply_fault(rule("http_500"))).status_code == 500


def test_route_scoping_and_method():
    reg = RuleRegistry()
    reg.activate(rule())
    assert find(reg, "a") and not find(reg, "b", path="/checkout")
    assert not find(reg, "c", method="POST") and not find(reg, "d", target_id=2)


def test_request_cap_counts_distinct_requests_not_retries():
    reg = RuleRegistry()
    reg.activate(rule())
    assert find(reg, "a") and find(reg, "a") and find(reg, "b")  # 'a' retried, still 2 distinct
    assert find(reg, "c") is None


def test_expiry_and_kill_switch():
    reg = RuleRegistry()
    reg.activate(rule(expires_at=time.time() - 1))
    assert find(reg, "a") is None and reg.active_rules() == []
    reg.activate(rule())
    reg.deactivate("e1")
    assert find(reg, "a") is None
