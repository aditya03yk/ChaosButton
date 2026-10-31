"""HTTP entry points of the fault-injection proxy.

/proxy/{target_id}/...  forwards to a registered target (inbound faults).
/upstream/...           forwards to the configured upstream dependency (dependency faults).
"""
import uuid

from fastapi import APIRouter, Depends, Request, Response

from app.api.dependencies import get_container, get_target_service
from app.container import Container
from app.services.target_service import TargetService

router = APIRouter(tags=["proxy"])
METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


async def _relay(request: Request, container: Container, *, scope: str, target_id, base_url: str, path: str) -> Response:
    request_id = request.headers.get("x-chaos-request-id") or uuid.uuid4().hex[:12]
    result = await container.gateway.forward(
        scope=scope, target_id=target_id, base_url=base_url, method=request.method, path=path,
        query=request.url.query, headers=dict(request.headers), body=await request.body(),
        request_id=request_id)
    if result.experiment_id:
        container.bus.publish(result.experiment_id, "proxy", {"scope": scope, "path": path,
                                                              "status_code": result.status_code,
                                                              "latency_ms": result.latency_ms})
    return Response(content=result.body, status_code=result.status_code, headers=result.headers)


@router.api_route("/proxy/{target_id}/{path:path}", methods=METHODS)
async def proxy_target(target_id: int, path: str, request: Request,
                       targets: TargetService = Depends(get_target_service),
                       container: Container = Depends(get_container)):
    target = targets.get(target_id)  # only registered (validated) targets can be proxied
    return await _relay(request, container, scope="inbound", target_id=target.id,
                        base_url=target.base_url, path="/" + path)


@router.api_route("/upstream/{path:path}", methods=METHODS)
async def proxy_upstream(path: str, request: Request, container: Container = Depends(get_container)):
    return await _relay(request, container, scope="dependency", target_id=None,
                        base_url=container.settings.upstream_url, path="/" + path)
