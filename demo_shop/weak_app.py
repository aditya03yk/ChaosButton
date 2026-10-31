"""WEAK demo shop (port 9001): deliberately lacks timeouts, retries and fallbacks.

Its dependency calls go through ChaosButton's /upstream gateway so faults can be injected.
"""
import os

import httpx
from fastapi import FastAPI, Request

UPSTREAM_URL = os.getenv("UPSTREAM_URL", "http://127.0.0.1:8000/upstream")

app = FastAPI(title="Demo shop (weak)")
# Weakness 1: no timeout at all. A slow dependency stalls every request.
client = httpx.AsyncClient(timeout=None)


def _trace_headers(request: Request) -> dict:
    return {"X-Chaos-Request-Id": request.headers.get("x-chaos-request-id", "")}


@app.get("/health")
async def health():
    return {"status": "ok", "variant": "weak"}


@app.get("/inventory")
async def inventory(request: Request):
    response = await client.get(f"{UPSTREAM_URL}/inventory", headers=_trace_headers(request))
    response.raise_for_status()  # Weakness 2: dependency errors become unhandled HTTP 500s
    return response.json()


@app.get("/product")
async def product(request: Request):
    stock = (await inventory(request))["stock"]
    return {"product": "Widget", "price": 19.99, "stock": stock}


@app.post("/checkout")
async def checkout(request: Request):
    response = await client.post(f"{UPSTREAM_URL}/payment", headers=_trace_headers(request))
    response.raise_for_status()  # Weakness 3: no fallback or user-facing error state
    return {"status": "paid"}
