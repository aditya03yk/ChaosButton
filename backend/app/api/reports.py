"""Report, dashboard and fix-workspace routes."""
from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.api.dependencies import get_container, get_report_service
from app.container import Container
from app.core.clock import utcnow
from app.core.errors import ConflictError, NotFoundError
from app.models.fixes import FIX_ORDER, FixStatus, FixUpdate
from app.services.report_service import ReportService
from app.storage.database import get_session
from app.storage.repositories import AnalysisRepository, FixRepository

router = APIRouter(tags=["reports"])


@router.get("/api/dashboard")
def dashboard(service: ReportService = Depends(get_report_service),
              container: Container = Depends(get_container)):
    return service.dashboard(container.orchestrator.active_count)


@router.get("/api/experiments/{experiment_id}/report")
def get_report(experiment_id: str, download: bool = False, response: Response = None,
               service: ReportService = Depends(get_report_service)):
    report = service.build_report(experiment_id)
    if download:
        response.headers["Content-Disposition"] = f'attachment; filename="{experiment_id}-report.json"'
    return report


@router.get("/api/experiments/{experiment_id}/fixes")
def list_fixes(experiment_id: str, session: Session = Depends(get_session)):
    analyses = {a.id: a for a in AnalysisRepository(session).list_for_experiment(experiment_id)}
    return [{"fix": f.model_dump(mode="json"), "analysis": analyses[f.analysis_id].model_dump(mode="json")}
            for f in FixRepository(session).list_for_experiment(experiment_id) if f.analysis_id in analyses]


@router.patch("/api/fixes/{fix_id}")
def update_fix(fix_id: int, body: FixUpdate, session: Session = Depends(get_session)):
    """Manual workflow: a fix may only advance one step (proposed -> reviewed -> applied -> verified)."""
    repo = FixRepository(session)
    fix = repo.get(fix_id)
    if fix is None:
        raise NotFoundError(f"Fix {fix_id} not found")
    if body.status is not None:
        current, target = FIX_ORDER.index(FixStatus(fix.status)), FIX_ORDER.index(body.status)
        if target not in (current, current + 1):
            raise ConflictError(f"A fix cannot move from {fix.status} to {body.status.value}")
        fix.status = body.status.value
    if body.developer_notes is not None:
        fix.developer_notes = body.developer_notes
    fix.updated_at = utcnow()
    return repo.save(fix).model_dump(mode="json")
