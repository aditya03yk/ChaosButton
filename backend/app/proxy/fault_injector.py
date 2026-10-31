"""Applies a matched fault rule to a request."""
import asyncio
from dataclasses import dataclass
from typing import Optional

from app.proxy.rules import FaultRule


@dataclass
class SyntheticResponse:
    """A response produced by the fault injector instead of the real target."""
    status_code: int
    body: bytes
    timed_out: bool = False
    error_category: Optional[str] = None


async def apply_fault(rule: FaultRule) -> Optional[SyntheticResponse]:
    """Apply the fault. Returns a synthetic response, or None to forward the request.

    - latency: delay, then let the request through unchanged.
    - timeout: hold the request for the timeout threshold, then answer 504 (never forwarded).
    - http_500 / http_503: answer immediately with that status.
    """
    if rule.fault_type == "latency":
        await asyncio.sleep((rule.delay_ms or 0) / 1000)
        return None
    if rule.fault_type == "timeout":
        await asyncio.sleep((rule.timeout_ms or 0) / 1000)
        return SyntheticResponse(504, b'{"error":"chaosbutton injected timeout"}',
                                 timed_out=True, error_category="timeout")
    if rule.fault_type in ("http_500", "http_503"):
        code = int(rule.fault_type.split("_")[1])
        return SyntheticResponse(code, b'{"error":"chaosbutton injected failure"}', error_category="http_5xx")
    return None
