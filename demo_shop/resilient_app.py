"""RESILIENT demo shop (port 9002): same endpoints, but with finite timeouts, bounded retries
with exponential backoff, a circuit breaker and graceful fallbacks."""
import asyncio
import os
import time
from typing import Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

UPSTREAM_URL = os.getenv("UPSTREAM_URL", "http://127.0.0.1:8000/upstream")
TIMEOUT_S, MAX_RETRIES, BACKOFF_S = 0.3, 2, 0.05
BREAKER_THRESHOLD, BREAKER_OPEN_S = 3, 2.0

app = FastAPI(title="Demo shop (resilient)")
client = httpx.AsyncClient(timeout=httpx.Timeout(TIMEOUT_S))  # finite timeout


class CircuitBreaker:
    """Opens after consecutive failed calls and short-circuits to the fallback for a while."""

    def __init__(self) -> None:
        self.failures, self.opened_at = 0, 0.0

    def is_open(self) -> bool:
        return time.monotonic() - self.opened_at < BREAKER_OPEN_S

    def record(self, ok: bool) -> None:
        self.failures = 0 if ok else self.failures + 1
        if self.failures >= BREAKER_THRESHOLD:
            self.opened_at, self.failures = time.monotonic(), 0


breaker = CircuitBreaker()


async def call_upstream(method: str, path: str, request: Request) -> Optional[httpx.Response]:
    """Return a good response, or None when the caller should use its fallback."""
    if breaker.is_open():
        return None
    headers = {"X-Chaos-Request-Id": request.headers.get("x-chaos-request-id", "")}
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.request(method, f"{UPSTREAM_URL}{path}", headers=headers)
        except httpx.TimeoutException:
            break  # a slow dependency will not get faster: do not retry timeouts
        except httpx.HTTPError:
            response = None
        if response is not None and response.status_code < 500:
            breaker.record(True)
            return response
        if attempt < MAX_RETRIES:
            await asyncio.sleep(BACKOFF_S * 2 ** attempt)  # exponential backoff
    breaker.record(False)
    return None


def fallback(body: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse({**body, "degraded": True}, status_code=status_code,
                        headers={"X-Fallback-Used": "true"})


@app.get("/health")
async def health():
    return {"status": "ok", "variant": "resilient"}


@app.get("/inventory")
async def inventory(request: Request):
    response = await call_upstream("GET", "/inventory", request)
    return response.json() if response else fallback({"sku": "WIDGET-1", "stock": None})


@app.get("/product")
async def product(request: Request):
    response = await call_upstream("GET", "/inventory", request)
    if response is None:
        return fallback({"product": "Widget", "price": 19.99, "stock": None})  # stock shown as "unknown"
    return {"product": "Widget", "price": 19.99, "stock": response.json()["stock"]}


@app.post("/checkout")
async def checkout(request: Request):
    response = await call_upstream("POST", "/payment", request)
    if response is None:  # never claim a payment succeeded; queue the order instead
        return fallback({"status": "pending", "message": "Payment is slow; your order is queued."}, 202)
    return {"status": "paid"}
