"""Experiment reports and the dashboard summary, built only from stored data."""
from sqlmodel import Session

from app.metrics.comparison import compare
from app.metrics.calculator import status_distribution
from app.services.experiment_service import ExperimentService
from app.storage.repositories import AnalysisRepository, FixRepository


class ReportService:
    def __init__(self, session: Session):
        self._svc = ExperimentService(session)
        self._analyses, self._fixes = AnalysisRepository(session), FixRepository(session)

    def build_report(self, experiment_id: str) -> dict:
        exp = self._svc.get(experiment_id)
        events = self._svc.events.list_requests(experiment_id)
        metrics = self._svc.metrics.get(experiment_id)
        retests = []
        for child in self._svc.experiments.list_children(experiment_id):
            child_metrics = self._svc.metrics.get(child.id)
            entry = {"experiment": self._svc.summary(child)}
            if metrics and child_metrics:
                entry["comparison"] = compare(exp, metrics, child, child_metrics)
            retests.append(entry)
        return {
            "experiment": self._svc.summary(exp),
            "target": self._svc.targets.get(exp.target_id).model_dump(mode="json"),
            "metrics": metrics.model_dump(mode="json") if metrics else None,
            "status_distribution": status_distribution([e for e in events if e.phase == "fault"]),
            "request_events": [e.model_dump(mode="json") for e in events],
            "timeline": [t.model_dump(mode="json") for t in self._svc.events.list_timeline(experiment_id)],
            "analyses": [a.model_dump(mode="json") for a in self._analyses.list_for_experiment(experiment_id)],
            "fixes": [f.model_dump(mode="json") for f in self._fixes.list_for_experiment(experiment_id)],
            "retests": retests,
            "disclaimer": "Indicative result from a small bounded sample; a comparative indicator, "
                          "not a reliability certification."}

    def dashboard(self, active_experiments: int) -> dict:
        items, total = self._svc.experiments.list(limit=6)
        all_metrics = self._svc.metrics.all()
        rates = [m.success_rate for m in all_metrics if m.success_rate is not None]
        scores = [m.resilience_score for m in all_metrics if m.resilience_score is not None]
        return {
            "total_experiments": total,
            "total_requests": self._svc.events.total_requests(),
            "average_success_rate": round(sum(rates) / len(rates), 2) if rates else None,
            "average_resilience_score": round(sum(scores) / len(scores), 2) if scores else None,
            "critical_findings": self._analyses.critical_count(),
            "last_experiment_status": items[0].status if items else None,
            "active_experiments": active_experiments,
            "recent_experiments": [self._svc.summary(e) for e in items[:5]],
            "activity": [t.model_dump(mode="json") for t in self._svc.events.recent_timeline(12)]}
