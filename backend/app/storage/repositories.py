"""Repositories: all database queries live here, never in route handlers."""
from typing import Optional, Sequence

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.clock import utcnow
from app.models.analysis import AIAnalysis
from app.models.events import RequestEvent, TimelineEvent
from app.models.experiment import Experiment, ExperimentStatus, TERMINAL_STATUSES
from app.models.fixes import FixRecord
from app.models.metrics import ExperimentMetrics
from app.models.target import Target


class BaseRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, obj):
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj


class TargetRepository(BaseRepository):
    def get(self, target_id: int) -> Optional[Target]:
        return self.session.get(Target, target_id)

    def list(self) -> Sequence[Target]:
        return self.session.exec(select(Target).order_by(col(Target.created_at).desc())).all()

    def delete(self, target: Target) -> None:
        self.session.delete(target)
        self.session.commit()

    def has_experiments(self, target_id: int) -> bool:
        stmt = select(func.count()).select_from(Experiment).where(Experiment.target_id == target_id)
        return self.session.exec(stmt).one() > 0


class ExperimentRepository(BaseRepository):
    def get(self, experiment_id: str) -> Optional[Experiment]:
        return self.session.get(Experiment, experiment_id)

    def list(self, *, target_id: Optional[int] = None, fault_type: Optional[str] = None,
             status: Optional[str] = None, search: Optional[str] = None,
             newest_first: bool = True, offset: int = 0, limit: int = 20):
        conditions = []
        if target_id:
            conditions.append(Experiment.target_id == target_id)
        if fault_type:
            conditions.append(Experiment.fault_type == fault_type)
        if status:
            conditions.append(Experiment.status == status)
        if search:
            conditions.append(col(Experiment.id).contains(search.strip()))
        total = self.session.exec(select(func.count()).select_from(Experiment).where(*conditions)).one()
        order = col(Experiment.created_at).desc() if newest_first else col(Experiment.created_at).asc()
        items = self.session.exec(select(Experiment).where(*conditions).order_by(order)
                                  .offset(offset).limit(limit)).all()
        return items, total

    def list_by_suite(self, suite_id: str) -> Sequence[Experiment]:
        stmt = select(Experiment).where(Experiment.suite_id == suite_id).order_by(col(Experiment.created_at))
        return self.session.exec(stmt).all()

    def list_children(self, experiment_id: str) -> Sequence[Experiment]:
        stmt = select(Experiment).where(Experiment.parent_experiment_id == experiment_id)
        return self.session.exec(stmt.order_by(col(Experiment.created_at))).all()

    def count_by_status(self, statuses: set[ExperimentStatus]) -> int:
        values = [s.value for s in statuses]
        stmt = select(func.count()).select_from(Experiment).where(col(Experiment.status).in_(values))
        return self.session.exec(stmt).one()

    def mark_interrupted(self) -> int:
        """Fail experiments left non-terminal by a restart (fault rules are in memory only)."""
        terminal = [s.value for s in TERMINAL_STATUSES] + [ExperimentStatus.CREATED.value]
        stale = self.session.exec(select(Experiment).where(col(Experiment.status).not_in(terminal))).all()
        for exp in stale:
            exp.status, exp.completed_at = ExperimentStatus.FAILED.value, utcnow()
            exp.error_message = "Interrupted by an application restart"
            self.session.add(exp)
        self.session.commit()
        return len(stale)


class EventRepository(BaseRepository):
    def add_requests(self, events: Sequence[RequestEvent]) -> None:
        self.session.add_all(events)
        self.session.commit()

    def list_requests(self, experiment_id: str, limit: int = 1000) -> Sequence[RequestEvent]:
        stmt = select(RequestEvent).where(RequestEvent.experiment_id == experiment_id)
        return self.session.exec(stmt.order_by(col(RequestEvent.timestamp)).limit(limit)).all()

    def add_timeline(self, event: TimelineEvent) -> TimelineEvent:
        return self.save(event)

    def list_timeline(self, experiment_id: str, limit: int = 200) -> Sequence[TimelineEvent]:
        stmt = select(TimelineEvent).where(TimelineEvent.experiment_id == experiment_id)
        return self.session.exec(stmt.order_by(col(TimelineEvent.timestamp)).limit(limit)).all()

    def recent_timeline(self, limit: int = 15) -> Sequence[TimelineEvent]:
        return self.session.exec(select(TimelineEvent).order_by(col(TimelineEvent.timestamp).desc())
                                 .limit(limit)).all()

    def total_requests(self) -> int:
        return self.session.exec(select(func.count()).select_from(RequestEvent)).one()


class MetricsRepository(BaseRepository):
    def get(self, experiment_id: str) -> Optional[ExperimentMetrics]:
        stmt = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == experiment_id)
        return self.session.exec(stmt).first()

    def upsert(self, metrics: ExperimentMetrics) -> ExperimentMetrics:
        existing = self.get(metrics.experiment_id)
        if existing:
            metrics.id = existing.id
            metrics = self.session.merge(metrics)
        return self.save(metrics)

    def all(self) -> Sequence[ExperimentMetrics]:
        return self.session.exec(select(ExperimentMetrics)).all()


class AnalysisRepository(BaseRepository):
    def list_for_experiment(self, experiment_id: str) -> Sequence[AIAnalysis]:
        stmt = select(AIAnalysis).where(AIAnalysis.experiment_id == experiment_id)
        return self.session.exec(stmt.order_by(col(AIAnalysis.created_at).desc())).all()

    def critical_count(self) -> int:
        stmt = select(func.count()).select_from(AIAnalysis).where(AIAnalysis.severity == "critical")
        return self.session.exec(stmt).one()


class FixRepository(BaseRepository):
    def get(self, fix_id: int) -> Optional[FixRecord]:
        return self.session.get(FixRecord, fix_id)

    def list_for_experiment(self, experiment_id: str) -> Sequence[FixRecord]:
        stmt = select(FixRecord).where(FixRecord.experiment_id == experiment_id)
        return self.session.exec(stmt.order_by(col(FixRecord.created_at).desc())).all()
