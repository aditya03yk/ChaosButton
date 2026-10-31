"""Builds evidence for Gemma, validates the result and stores it as a fix proposal."""
from typing import Optional

from sqlmodel import Session

from app.ai.provider import AIProvider
from app.core.errors import ConflictError, NotFoundError
from app.models.analysis import AIAnalysis
from app.models.experiment import Experiment
from app.models.fixes import FixRecord
from app.models.metrics import ExperimentMetrics
from app.models.target import Target
from app.storage.repositories import (AnalysisRepository, EventRepository, ExperimentRepository,
                                      FixRepository, MetricsRepository, TargetRepository)


def severity_hint(m: ExperimentMetrics) -> str:
    """Deterministic starting point for severity (the model must still justify its choice)."""
    error_rate, success = m.error_rate or 0, m.success_rate if m.success_rate is not None else 100
    slowed = bool(m.baseline_p95_latency and m.p95_latency and m.p95_latency > 3 * m.baseline_p95_latency)
    if error_rate >= 50 or success < 50:
        return "critical"
    if error_rate >= 20:
        return "high"
    return "medium" if error_rate > 0 or slowed else "low"


def build_evidence(exp: Experiment, target: Target, m: ExperimentMetrics, timeline: list[str]) -> dict:
    unavailable = "unavailable"
    return {
        "experiment": {"id": exp.id, "fault_type": exp.fault_type, "route": exp.route, "method": exp.method,
                       "target": target.name, "declared_stack": target.technology_stack,
                       "fault_parameters": exp.fault_configuration},
        "measured": {
            "fault_period_requests": m.total_requests, "success_rate_pct": m.success_rate,
            "error_rate_pct": m.error_rate, "timeouts": m.timeout_count, "p50_latency_ms": m.p50_latency,
            "p95_latency_ms": m.p95_latency, "baseline_p50_latency_ms": m.baseline_p50_latency,
            "baseline_p95_latency_ms": m.baseline_p95_latency,
            "fallback_score_pct": m.fallback_score if m.fallback_score is not None else unavailable,
            "recovery_time_s": m.recovery_time if m.recovery_time is not None else unavailable,
            "resilience_score": m.resilience_score},
        "timeline": timeline, "limitations": m.limitations, "deterministic_severity_hint": severity_hint(m)}


class AIService:
    def __init__(self, provider: AIProvider, session: Session):
        self._provider, self._session = provider, session

    async def analyse(self, experiment_id: str, code_context: Optional[str] = None) -> tuple[AIAnalysis, FixRecord]:
        exp = ExperimentRepository(self._session).get(experiment_id)
        if exp is None:
            raise NotFoundError(f"Experiment {experiment_id} not found")
        metrics = MetricsRepository(self._session).get(experiment_id)
        if metrics is None:
            raise ConflictError("This experiment has no measurements yet; run it before analysing.")
        target = TargetRepository(self._session).get(exp.target_id)
        timeline = [f"{e.timestamp:%H:%M:%S} [{e.level}] {e.message}"
                    for e in EventRepository(self._session).list_timeline(experiment_id, 20)]
        evidence = build_evidence(exp, target, metrics, timeline)
        if code_context:
            evidence["code_context"] = code_context
        result = await self._provider.generate_analysis(evidence)
        analysis = AnalysisRepository(self._session).save(AIAnalysis(
            experiment_id=experiment_id, model_name=self._provider.model_name, finding=result.finding,
            severity=result.severity.value, severity_rationale=result.severity_rationale,
            what_happened=result.what_happened, user_impact=result.user_impact, evidence=result.evidence,
            likely_cause=result.likely_cause, recommended_actions=result.recommended_actions,
            code_example=result.code_example.model_dump(), verification_steps=result.verification_steps))
        fix = FixRepository(self._session).save(FixRecord(experiment_id=experiment_id, analysis_id=analysis.id))
        return analysis, fix
