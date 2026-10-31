"""FastAPI dependencies."""
from fastapi import Depends, Request
from sqlmodel import Session

from app.container import Container
from app.services.experiment_service import ExperimentService
from app.services.report_service import ReportService
from app.services.target_service import TargetService
from app.storage.database import get_session


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_target_service(session: Session = Depends(get_session),
                       container: Container = Depends(get_container)) -> TargetService:
    return TargetService(session, container.settings, container.http)


def get_experiment_service(session: Session = Depends(get_session)) -> ExperimentService:
    return ExperimentService(session)


def get_report_service(session: Session = Depends(get_session)) -> ReportService:
    return ReportService(session)
