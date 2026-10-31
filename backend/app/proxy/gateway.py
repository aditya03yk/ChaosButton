"""Forwarding proxy with fault injection (FastAPI-agnostic, built on httpx)."""
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.proxy.fault_injector import apply_fault
from app.proxy.route_matcher import normalize_path
from app.proxy.rules import RuleRegistry

logger = logging.getLogger(__name__)

HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te",
              "trailers", "transfer-encoding", "upgrade", "host", "content-length", "content-encoding"}


@dataclass
class ProxyResult:
    status_code: int
    headers: dict = field(default_factory=dict)
    body: bytes = b""
    latency_ms: float = 0.0
    fault_applied: bool = False
    timed_out: bool = False
    error_category: Optional[str] = None
    experiment_id: Optional[str] = None

    @property
    def fallback_used(self) -> bool:
        return self.headers.get("x-fallback-used", "").lower() == "true"


def _clean_headers(headers: dict) -> dict:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP}


class ProxyGateway:
    def __init__(self, registry: RuleRegistry, client: httpx.AsyncClient, default_timeout_s: float):
        self._registry = registry
        self._client = client
        self._default_timeout_s = default_timeout_s

    async def forward(self, *, scope: Optional[str], target_id: Optional[int], base_url: str,
                      method: str, path: str, query: str = "", headers: Optional[dict] = None,
                      body: bytes = b"", request_id: str = "", timeout_s: Optional[float] = None) -> ProxyResult:
        """Forward one request. scope=None bypasses fault lookup (plain forwarding)."""
        started = time.perf_counter()
        rule = None
        if scope is not None:
            rule = self._registry.find(scope=scope, target_id=target_id, method=method,
                                       path=path, request_id=request_id)
        experiment_id = rule.experiment_id if rule else None
        if rule:
            synthetic = await apply_fault(rule)
            if synthetic:
                return ProxyResult(synthetic.status_code, {"content-type": "application/json"}, synthetic.body,
                                   _elapsed_ms(started), True, synthetic.timed_out,
                                   synthetic.error_category, experiment_id)
        url = base_url.rstrip("/") + normalize_path(path) + (f"?{query}" if query else "")
        result = await self._send(method, url, headers or {}, body, timeout_s or self._default_timeout_s)
        result.latency_ms = _elapsed_ms(started)
        result.fault_applied, result.experiment_id = rule is not None, experiment_id
        return result

    async def _send(self, method: str, url: str, headers: dict, body: bytes, timeout_s: float) -> ProxyResult:
        try:
            # Redirects are never followed: they could bypass the target allow-list.
            response = await self._client.request(method, url, headers=_clean_headers(headers),
                                                  content=body or None, timeout=timeout_s,
                                                  follow_redirects=False)
        except httpx.TimeoutException:
            return ProxyResult(504, timed_out=True, error_category="timeout")
        except httpx.HTTPError as exc:
            logger.warning("proxy upstream error: %s", type(exc).__name__)
            return ProxyResult(502, error_category="connection_error")
        return ProxyResult(response.status_code, _clean_headers(dict(response.headers)), response.content,
                           error_category=_categorize(response.status_code))


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _categorize(status: int) -> Optional[str]:
    if status >= 500:
        return "http_5xx"
    return "http_4xx" if status >= 400 else None
