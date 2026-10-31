"""Upstream dependency used by both demo shops (inventory + payment). Port 9100."""
import asyncio

from fastapi import FastAPI

app = FastAPI(title="Demo upstream (inventory/payment)")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/inventory")
async def inventory():
    await asyncio.sleep(0.02)  # normal dependency latency
    return {"sku": "WIDGET-1", "stock": 42}


@app.post("/payment")
async def payment():
    await asyncio.sleep(0.02)
    return {"status": "authorised"}
