"""Experiment, suite, streaming, analysis and comparison routes."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.ai.provider import AIError
from app.ai.schemas import AnalysisRequest
from app.ai.service import AIService
from app.api.dependencies import get_container, get_experiment_service
from app.container import Container
from app.core.errors import ConflictError
from app.metrics.comparison import compare
from app.models.experiment import (AutoSuiteRequest, CompareRequest, ExperimentCreate, RetestRequest)
from app.services.experiment_service import ExperimentService
from app.storage.database import get_session

router = APIRouter(tags=["experiments"])


@router.post("/api/experiments", status_code=201)
def create_experiment(body: ExperimentCreate, svc: ExperimentService = Depends(get_experiment_service)):
    return svc.summary(svc.create(body))


@router.get("/api/experiments")
def list_experiments(target_id: Optional[int] = None, fault_type: Optional[str] = None,
                     status: Optional[str] = None, search: Optional[str] = None, newest_first: bool = True,
                     offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                     svc: ExperimentService = Depends(get_experiment_service)):
    items, total = svc.experiments.list(target_id=target_id, fault_type=fault_type, status=status,
                                        search=search, newest_first=newest_first, offset=offset, limit=limit)
    return {"items": [svc.summary(e) for e in items], "total": total, "offset": offset, "limit": limit}


@router.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: str, svc: ExperimentService = Depends(get_experiment_service)):
    return svc.summary(svc.get(experiment_id))


@router.post("/api/experiments/{experiment_id}/start", status_code=202)
async def start_experiment(experiment_id: str, svc: ExperimentService = Depends(get_experiment_service),
                     container: Container = Depends(get_container)):
    svc.get(experiment_id)
    container.orchestrator.start(experiment_id)
    container.bus.publish(experiment_id, "status", {"status": "CREATED"})  # opens the stream channel
    return svc.summary(svc.get(experiment_id))


@router.post("/api/experiments/{experiment_id}/stop")
async def stop_experiment(experiment_id: str, svc: ExperimentService = Depends(get_experiment_service),
                          container: Container = Depends(get_container)):
    svc.get(experiment_id)
    await container.orchestrator.stop(experiment_id)
    return svc.summary(svc.get(experiment_id))


@router.get("/api/experiments/{experiment_id}/events")
def get_events(experiment_id: str, limit: int = Query(1000, ge=1, le=5000),
               svc: ExperimentService = Depends(get_experiment_service)):
    svc.get(experiment_id)
    return {"requests": [e.model_dump(mode="json") for e in svc.events.list_requests(experiment_id, limit)],
            "timeline": [t.model_dump(mode="json") for t in svc.events.list_timeline(experiment_id)]}


@router.get("/api/experiments/{experiment_id}/stream")
async def stream_events(experiment_id: str, request: Request,
                        svc: ExperimentService = Depends(get_experiment_service),
                        container: Container = Depends(get_container)):
    exp = svc.get(experiment_id)
    try:
        last_id = int(request.headers.get("last-event-id", "0"))
    except ValueError:
        last_id = 0

    def frame(event_id: int, name: str, data) -> str:
        return f"id: {event_id}\nevent: {name}\ndata: {json.dumps(data, default=str)}\n\n"

    async def generate():
        if not container.bus.has_channel(experiment_id):  # finished before a restart, or not started
            yield frame(0, "status", {"status": exp.status, "message": exp.error_message})
            return
        async for event in container.bus.subscribe(experiment_id, last_id):
            yield ": keepalive\n\n" if event is None else frame(event.id, event.type, event.data)

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/api/experiments/{experiment_id}/ai-analysis", status_code=201)
async def analyse_experiment(experiment_id: str, body: AnalysisRequest = AnalysisRequest(),
                             session: Session = Depends(get_session), container: Container = Depends(get_container)):
    analysis, fix = await AIService(container.ai_provider, session).analyse(experiment_id, body.code_context)
    return {"analysis": analysis.model_dump(mode="json"), "fix": fix.model_dump(mode="json")}


@router.post("/api/experiments/{experiment_id}/compare")
async def compare_experiments(experiment_id: str, body: CompareRequest,
                              svc: ExperimentService = Depends(get_experiment_service),
                              container: Container = Depends(get_container)):
    a, b = svc.get(experiment_id), svc.get(body.other_experiment_id)
    ma, mb = svc.metrics.get(a.id), svc.metrics.get(b.id)
    if ma is None or mb is None:
        raise ConflictError("Both experiments need measurements before they can be compared.")
    result = compare(a, ma, b, mb)
    if body.explain:
        try:
            validation = await container.ai_provider.generate_fix_validation(result)
            result["ai_validation"] = validation.model_dump()
        except AIError as exc:
            result["ai_validation_error"] = exc.message
    return result


@router.post("/api/experiments/{experiment_id}/retest", status_code=201)
def retest_experiment(experiment_id: str, body: RetestRequest = RetestRequest(),
                      svc: ExperimentService = Depends(get_experiment_service)):
    return svc.summary(svc.retest(experiment_id, body.target_id))


@router.post("/api/suites", status_code=201)
async def start_auto_suite(body: AutoSuiteRequest, svc: ExperimentService = Depends(get_experiment_service),
                     container: Container = Depends(get_container)):
    suite_id, created = svc.create_suite(body)
    ids = [e.id for e in created]
    container.orchestrator.start_suite(suite_id, ids)
    for experiment_id in ids:
        container.bus.publish(experiment_id, "status", {"status": "CREATED"})
    return svc.suite_summary(suite_id)


@router.get("/api/suites/{suite_id}")
def get_suite(suite_id: str, svc: ExperimentService = Depends(get_experiment_service)):
    return svc.suite_summary(suite_id)


@router.post("/api/suites/{suite_id}/stop")
async def stop_suite(suite_id: str, svc: ExperimentService = Depends(get_experiment_service),
                     container: Container = Depends(get_container)):
    await container.orchestrator.stop_suite(suite_id)
    return svc.suite_summary(suite_id)
