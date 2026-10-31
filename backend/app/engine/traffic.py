"""Sends one measured request through the proxy gateway on behalf of the runner."""
from dataclasses import dataclass
from typing import Optional

from app.core.clock import utcnow
from app.proxy.gateway import ProxyGateway


@dataclass
class RequestOutcome:
    timestamp: object
    status_code: Optional[int]
    latency_ms: float
    success: bool
    timed_out: bool
    fault_applied: bool
    fallback_used: bool
    error_category: Optional[str]


class TrafficClient:
    def __init__(self, gateway: ProxyGateway):
        self._gateway = gateway

    async def send(self, *, fault_scope: Optional[str], target_id: int, base_url: str, method: str,
                   route: str, request_id: str, timeout_s: float) -> RequestOutcome:
        """fault_scope='inbound' routes through fault matching; None forwards without it
        (dependency-scoped faults are applied by the target's own calls to /upstream)."""
        started = utcnow()
        result = await self._gateway.forward(
            scope=fault_scope, target_id=target_id, base_url=base_url, method=method, path=route,
            headers={"X-Chaos-Request-Id": request_id}, request_id=request_id, timeout_s=timeout_s)
        success = not result.timed_out and result.status_code < 400
        return RequestOutcome(started, result.status_code, result.latency_ms, success, result.timed_out,
                              result.fault_applied, result.fallback_used, result.error_category)
