"""Experiment creation, retest, suites and summaries."""
from typing import Optional
from uuid import uuid4

from sqlmodel import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.events import TimelineEvent
from app.models.experiment import (Experiment, ExperimentCreate, ExperimentMode, FaultParams,
                                   FaultType, AutoSuiteRequest, TERMINAL_STATUSES, ExperimentStatus)
from app.storage.repositories import (EventRepository, ExperimentRepository, MetricsRepository,
                                      TargetRepository)

AUTO_SCENARIOS = [(FaultType.LATENCY, {"delay_ms": 500}), (FaultType.TIMEOUT, {"timeout_ms": 2000}),
                  (FaultType.HTTP_503, {})]


class ExperimentService:
    def __init__(self, session: Session):
        self.experiments = ExperimentRepository(session)
        self.metrics = MetricsRepository(session)
        self.events = EventRepository(session)
        self.targets = TargetRepository(session)

    def get(self, experiment_id: str) -> Experiment:
        exp = self.experiments.get(experiment_id)
        if exp is None:
            raise NotFoundError(f"Experiment {experiment_id} not found")
        return exp

    def create(self, data: ExperimentCreate) -> Experiment:
        target = self.targets.get(data.target_id)
        if target is None:
            raise NotFoundError(f"Target {data.target_id} not found")
        if data.parent_experiment_id:
            self.get(data.parent_experiment_id)
        exp = Experiment(
            target_id=target.id, suite_id=data.suite_id, mode=data.mode.value, route=data.route,
            method=data.method, fault_type=data.fault_type.value, notes=data.notes,
            name=data.name or f"{data.fault_type.value} on {target.name}",
            fault_configuration=data.fault_configuration.model_dump(mode="json"),
            parent_experiment_id=data.parent_experiment_id)
        exp = self.experiments.save(exp)
        self.events.add_timeline(TimelineEvent(experiment_id=exp.id, kind="created", level="info",
                                               message=f"Experiment {exp.id} created ({exp.name})"))
        return exp

    def create_suite(self, req: AutoSuiteRequest) -> tuple[str, list[Experiment]]:
        suite_id = f"suite_{uuid4().hex[:8]}"
        created = []
        for fault_type, extra in AUTO_SCENARIOS:
            params = FaultParams(scope=req.scope, dependency_route=req.dependency_route, max_affected=10,
                                 baseline_requests=10, concurrency=2, **extra)
            created.append(self.create(ExperimentCreate(
                target_id=req.target_id, mode=ExperimentMode.AUTO, route=req.route, method=req.method,
                fault_type=fault_type, fault_configuration=params, suite_id=suite_id)))
        return suite_id, created

    def retest(self, experiment_id: str, target_id: Optional[int]) -> Experiment:
        original = self.get(experiment_id)
        if ExperimentStatus(original.status) not in TERMINAL_STATUSES:
            raise ConflictError("Only finished experiments can be retested")
        return self.create(ExperimentCreate(
            target_id=target_id or original.target_id, mode=ExperimentMode(original.mode), route=original.route,
            method=original.method, fault_type=FaultType(original.fault_type),
            fault_configuration=FaultParams(**original.fault_configuration),
            notes=f"Retest of {original.id}", parent_experiment_id=original.id))

    def summary(self, exp: Experiment) -> dict:
        target = self.targets.get(exp.target_id)
        metrics = self.metrics.get(exp.id)
        return {**exp.model_dump(mode="json"), "target_name": target.name if target else None,
                "metrics": metrics.model_dump(mode="json") if metrics else None}

    def suite_summary(self, suite_id: str) -> dict:
        members = self.experiments.list_by_suite(suite_id)
        if not members:
            raise NotFoundError(f"Suite {suite_id} not found")
        items = [self.summary(e) for e in members]
        done = [i["metrics"] for i in items if i["metrics"]]
        scored = [(i["fault_type"], i["metrics"]["resilience_score"]) for i in items
                  if i["metrics"] and i["metrics"]["resilience_score"] is not None]
        finished = all(ExperimentStatus(e.status) in TERMINAL_STATUSES for e in members)
        return {"suite_id": suite_id, "experiments": items, "finished": finished,
                "consolidated": {
                    "scenarios_completed": sum(1 for e in members if e.status == "COMPLETED"),
                    "scenarios_total": len(members),
                    "average_success_rate": _avg([m["success_rate"] for m in done]),
                    "average_resilience_score": _avg([s for _, s in scored]),
                    "weakest_scenario": min(scored, key=lambda x: x[1])[0] if scored else None}}


def _avg(values: list) -> Optional[float]:
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 2) if values else None
