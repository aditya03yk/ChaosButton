"""Executes one experiment: validate -> baseline -> fault -> recovery -> metrics."""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from app.core.clock import utcnow
from app.core.config import Settings
from app.engine.event_bus import EventBus
from app.engine.state_manager import assert_transition
from app.engine.traffic import RequestOutcome, TrafficClient
from app.metrics.calculator import build_experiment_metrics, live_snapshot, summarize
from app.models.events import RequestEvent, TimelineEvent
from app.models.experiment import TERMINAL_STATUSES, ExperimentStatus as S, FaultParams
from app.models.metrics import ExperimentMetrics
from app.proxy.rules import FaultRule, RuleRegistry
from app.services.target_service import validate_url
from app.storage.database import session_scope
from app.storage.repositories import EventRepository, ExperimentRepository, MetricsRepository, TargetRepository

logger = logging.getLogger(__name__)


class RunnerError(Exception):
    """A controlled failure with a user-safe message."""


@dataclass
class RunContext:
    experiment_id: str
    target_id: int
    base_url: str
    ownership_confirmed: bool
    environment_type: str
    method: str
    route: str
    fault_type: str
    params: FaultParams
    events: list[RequestEvent] = field(default_factory=list)
    flushed: int = 0
    started_at: Optional[object] = None
    fault_removed_at: Optional[object] = None
    phase: str = "baseline"


class ExperimentRunner:
    def __init__(self, settings: Settings, registry: RuleRegistry, bus: EventBus, traffic: TrafficClient, http):
        self._settings, self._registry, self._bus = settings, registry, bus
        self._traffic, self._http = traffic, http

    async def run(self, experiment_id: str) -> None:
        """Run to completion. Never leaves a fault rule active, whatever happens."""
        ctx = self._load_context(experiment_id)
        try:
            await asyncio.wait_for(self._execute(ctx), timeout=self._settings.max_experiment_duration + 60)
        except asyncio.CancelledError:
            self._registry.deactivate(experiment_id)
            self._finish(ctx, S.STOPPED, "Stopped by the operator")
            raise
        except asyncio.TimeoutError:
            self._finish(ctx, S.FAILED, "Experiment exceeded the maximum allowed duration")
        except RunnerError as exc:
            self._finish(ctx, S.FAILED, str(exc))
        except Exception:  # noqa: BLE001 - last line of defence; details go to the log only
            logger.exception("experiment %s crashed", experiment_id)
            self._finish(ctx, S.FAILED, "Unexpected internal error (see server log)")
        finally:
            self._registry.deactivate(experiment_id)

    # ---- phases -----------------------------------------------------------------------------
    async def _execute(self, ctx: RunContext) -> None:
        p = ctx.params
        ctx.started_at = utcnow()
        self._update(ctx, started_at=ctx.started_at)
        self._set_status(ctx, S.VALIDATING)
        await self._validate_target(ctx)

        self._set_status(ctx, S.BASELINE)
        self._emit(ctx, "info", "baseline", f"Baseline started ({p.baseline_requests} requests)")
        await self._send(ctx, "baseline", p.baseline_requests, concurrency=1, interval_ms=50)
        baseline = summarize([e for e in ctx.events if e.phase == "baseline"])
        if not baseline["successful"]:
            raise RunnerError("Baseline failed: the target returned no successful responses")
        self._emit(ctx, "success", "baseline", f"Baseline completed (p95 {baseline['p95_latency']} ms)")
        self._flush(ctx)

        self._set_status(ctx, S.RUNNING)
        rule = self._activate_rule(ctx)
        await self._send(ctx, "fault", p.max_affected, concurrency=p.concurrency,
                         interval_ms=p.interval_ms, deadline=rule.expires_at)
        self._registry.deactivate(ctx.experiment_id)
        ctx.fault_removed_at = utcnow()
        self._emit(ctx, "info", "fault", f"Fault injection stopped ({rule.affected_count} requests affected)")
        self._flush(ctx)

        self._set_status(ctx, S.RECOVERING)
        await self._send(ctx, "recovery", self._settings.recovery_probe_count, concurrency=1,
                         interval_ms=self._settings.recovery_probe_interval_ms)
        self._finish(ctx, S.COMPLETED)

    async def _validate_target(self, ctx: RunContext) -> None:
        result = await validate_url(ctx.base_url, ctx.ownership_confirmed, ctx.environment_type,
                                    self._settings, self._http)
        if not result.valid:
            raise RunnerError("Target validation failed: " + "; ".join(result.errors))
        self._emit(ctx, "success", "validation", "Target validated")

    def _activate_rule(self, ctx: RunContext) -> FaultRule:
        p = ctx.params
        rule = FaultRule(
            experiment_id=ctx.experiment_id, target_id=ctx.target_id, scope=p.scope.value,
            route=p.dependency_route if p.scope.value == "dependency" else ctx.route,
            method="*" if p.scope.value == "dependency" else ctx.method, fault_type=ctx.fault_type,
            max_affected=p.max_affected, expires_at=time.time() + p.duration_s,
            delay_ms=p.delay_ms, timeout_ms=p.timeout_ms)
        self._registry.activate(rule)
        self._emit(ctx, "warning", "fault", f"{ctx.fault_type} fault activated on {rule.route} "
                   f"(cap {p.max_affected} requests, expires in {p.duration_s}s)")
        return rule

    # ---- traffic ----------------------------------------------------------------------------
    async def _send(self, ctx: RunContext, phase: str, count: int, *, concurrency: int,
                    interval_ms: int, deadline: Optional[float] = None) -> None:
        ctx.phase = phase
        semaphore = asyncio.Semaphore(concurrency)

        async def one() -> None:
            async with semaphore:
                if deadline is not None and time.time() >= deadline:
                    return  # fault expired server-side: stop sending affected traffic
                request_id = uuid.uuid4().hex[:12]
                outcome = await self._traffic.send(
                    fault_scope="inbound" if ctx.params.scope.value == "inbound" else None,
                    target_id=ctx.target_id, base_url=ctx.base_url, method=ctx.method, route=ctx.route,
                    request_id=request_id, timeout_s=ctx.params.request_timeout_ms / 1000)
                if phase == "fault":
                    outcome.fault_applied = self._registry.was_affected(ctx.experiment_id, request_id) \
                        or outcome.fault_applied
                self._record(ctx, phase, outcome)
                await asyncio.sleep(interval_ms / 1000)

        await asyncio.gather(*(one() for _ in range(count)))

    def _record(self, ctx: RunContext, phase: str, outcome: RequestOutcome) -> None:
        event = RequestEvent(
            experiment_id=ctx.experiment_id, timestamp=outcome.timestamp, phase=phase, route=ctx.route,
            method=ctx.method, status_code=outcome.status_code, latency_ms=outcome.latency_ms,
            success=outcome.success, timed_out=outcome.timed_out, fault_applied=outcome.fault_applied,
            fallback_used=outcome.fallback_used, error_category=outcome.error_category)
        ctx.events.append(event)
        self._bus.publish(ctx.experiment_id, "request", event.model_dump(mode="json"))
        if phase == "fault":
            active = len(self._registry.active_rules())
            self._bus.publish(ctx.experiment_id, "metrics", live_snapshot(
                [e for e in ctx.events if e.phase == "fault"], active_faults=active,
                started_at=ctx.started_at, now=utcnow(), phase=phase))

    # ---- persistence and events -------------------------------------------------------------
    def _load_context(self, experiment_id: str) -> RunContext:
        with session_scope() as session:
            exp = ExperimentRepository(session).get(experiment_id)
            target = TargetRepository(session).get(exp.target_id)
            return RunContext(experiment_id, target.id, target.base_url, target.ownership_confirmed,
                              target.environment_type, exp.method, exp.route, exp.fault_type,
                              FaultParams(**exp.fault_configuration))

    def _update(self, ctx: RunContext, **fields) -> None:
        with session_scope() as session:
            repo = ExperimentRepository(session)
            exp = repo.get(ctx.experiment_id)
            for key, value in fields.items():
                setattr(exp, key, value)
            repo.save(exp)

    def _set_status(self, ctx: RunContext, new: S) -> None:
        with session_scope() as session:
            repo = ExperimentRepository(session)
            exp = repo.get(ctx.experiment_id)
            assert_transition(S(exp.status), new)  # raises if e.g. the kill switch already stopped it
            exp.status = new.value
            repo.save(exp)
        self._bus.publish(ctx.experiment_id, "status", {"status": new.value})

    def _emit(self, ctx: RunContext, level: str, kind: str, message: str) -> None:
        event = TimelineEvent(experiment_id=ctx.experiment_id, level=level, kind=kind, message=message)
        with session_scope() as session:
            EventRepository(session).add_timeline(event)
        self._bus.publish(ctx.experiment_id, "timeline", event.model_dump(mode="json"))

    def _flush(self, ctx: RunContext) -> None:
        pending = ctx.events[ctx.flushed:]
        if pending:
            with session_scope() as session:
                EventRepository(session).add_requests(pending)
            ctx.flushed = len(ctx.events)

    def _finish(self, ctx: RunContext, status: S, message: Optional[str] = None) -> None:
        """Persist final state and metrics, notify clients. Idempotent for terminal states."""
        self._flush(ctx)
        metrics = build_experiment_metrics(ctx.events, ctx.fault_removed_at)
        with session_scope() as session:
            if metrics:
                MetricsRepository(session).upsert(ExperimentMetrics(experiment_id=ctx.experiment_id, **metrics))
            repo = ExperimentRepository(session)
            exp = repo.get(ctx.experiment_id)
            if S(exp.status) not in TERMINAL_STATUSES:
                exp.status, exp.error_message = status.value, (message if status is not S.COMPLETED else None)
            exp.completed_at = exp.completed_at or utcnow()
            if ctx.started_at:
                exp.duration = round((exp.completed_at - ctx.started_at).total_seconds(), 2)
            repo.save(exp)
            final = exp.status
        level = {"COMPLETED": "success", "STOPPED": "warning"}.get(final, "error")
        self._emit(ctx, level, "status", message or f"Experiment {final.lower()}")
        self._bus.publish(ctx.experiment_id, "status", {"status": final, "message": message})
        self._bus.close(ctx.experiment_id)
