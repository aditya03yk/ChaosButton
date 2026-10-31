"""Target management routes."""
from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_container, get_target_service
from app.container import Container
from app.models.target import (EnvironmentType, Target, TargetCreate, TargetUpdate,
                               TechStack, ValidationRequest, ValidationResult)
from app.services.target_service import TargetService, validate_url

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.post("/validate", response_model=ValidationResult)
async def validate_target(body: ValidationRequest, container: Container = Depends(get_container)):
    return await validate_url(body.base_url, body.ownership_confirmed, body.environment_type.value,
                              container.settings, container.http)


@router.post("/demo", response_model=list[Target])
async def add_demo_targets(service: TargetService = Depends(get_target_service)):
    """Create the bundled loopback demo targets once; repeated calls are safe."""
    demos = [
        TargetCreate(name="Demo shop (weak)", base_url="http://127.0.0.1:9001",
                     description="No timeouts, retries or fallbacks", technology_stack=TechStack.PYTHON_FASTAPI,
                     environment_type=EnvironmentType.DEMO),
        TargetCreate(name="Demo shop (resilient)", base_url="http://127.0.0.1:9002",
                     description="Timeouts, retries, circuit breaker and fallbacks",
                     technology_stack=TechStack.PYTHON_FASTAPI, environment_type=EnvironmentType.DEMO),
    ]
    existing = {target.base_url.rstrip("/"): target for target in service.list()}
    result = []
    for demo in demos:
        key = demo.base_url.rstrip("/")
        target = existing.get(key)
        if target is None:
            target = await service.create(demo)
            existing[key] = target
        result.append(target)
    return result


@router.post("", response_model=Target, status_code=201)
async def create_target(body: TargetCreate, service: TargetService = Depends(get_target_service)):
    return await service.create(body)


@router.get("", response_model=list[Target])
def list_targets(service: TargetService = Depends(get_target_service)):
    return service.list()


@router.get("/{target_id}", response_model=Target)
def get_target(target_id: int, service: TargetService = Depends(get_target_service)):
    return service.get(target_id)


@router.patch("/{target_id}", response_model=Target)
async def update_target(target_id: int, body: TargetUpdate, service: TargetService = Depends(get_target_service)):
    return await service.update(target_id, body)


@router.delete("/{target_id}", status_code=204)
def delete_target(target_id: int, service: TargetService = Depends(get_target_service)):
    service.delete(target_id)
    return Response(status_code=204)


@router.post("/{target_id}/validate", response_model=ValidationResult)
async def revalidate_target(target_id: int, service: TargetService = Depends(get_target_service)):
    return await service.revalidate(target_id)
