"""Health and system status routes."""
from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.container import Container
from app.storage.database import database_ok

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/api/system/ai-status")
async def ai_status(container: Container = Depends(get_container)):
    return await container.ai_provider.status()


@router.get("/api/system/status")
async def system_status(container: Container = Depends(get_container)):
    ai = await container.ai_provider.status()
    return {"backend": "ok", "database": "ok" if database_ok() else "error", "ai": ai.model_dump(),
            "active_experiments": container.orchestrator.active_count}


@router.get("/api/system/config")
def system_config(container: Container = Depends(get_container)):
    return container.settings.public_dict()
