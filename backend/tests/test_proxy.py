"""Route matching and the forwarding gateway (httpx mock transport, no network)."""
import asyncio
import time

import httpx

from app.proxy.gateway import ProxyGateway
from app.proxy.route_matcher import matches, method_matches, normalize_path
from app.proxy.rules import FaultRule, RuleRegistry


def test_route_matching():
    assert normalize_path("product/?x=1") == "/product"
    assert matches("/product", "/product/") and not matches("/product", "/products")
    assert matches("/api/*", "/api/items/1") and not matches("/api/*", "/apix")
    assert method_matches("*", "POST") and not method_matches("GET", "POST")


def make_gateway(registry):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"path": request.url.path},
                              headers={"X-Fallback-Used": "true", "Connection": "close"})
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ProxyGateway(registry, client, 2.0)


def forward(gateway, scope="inbound", **kw):
    args = dict(scope=scope, target_id=1, base_url="http://t", method="GET", path="/product", request_id="r1")
    return asyncio.run(gateway.forward(**{**args, **kw}))


def test_forwards_normally_without_active_rule_and_strips_hop_headers():
    result = forward(make_gateway(RuleRegistry()))
    assert result.status_code == 200 and not result.fault_applied and result.fallback_used
    assert "connection" not in result.headers


def test_applies_matching_fault_and_ignores_other_routes():
    registry = RuleRegistry()
    registry.activate(FaultRule("e", 1, "inbound", "/product", "GET", "http_503", 5, time.time() + 10))
    gateway = make_gateway(registry)
    hit, miss = forward(gateway), forward(gateway, path="/checkout", request_id="r2")
    assert hit.status_code == 503 and hit.fault_applied and hit.experiment_id == "e"
    assert miss.status_code == 200 and not miss.fault_applied


def test_upstream_errors_become_502_and_timeouts_504():
    def boom(request):
        raise httpx.ConnectError("refused")
    gateway = ProxyGateway(RuleRegistry(), httpx.AsyncClient(transport=httpx.MockTransport(boom)), 1.0)
    result = forward(gateway)
    assert result.status_code == 502 and result.error_category == "connection_error"
