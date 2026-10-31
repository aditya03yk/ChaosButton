"""Starts and stops experiments and auto-test suites (the kill switch lives here)."""
import asyncio
import logging

from app.core.clock import utcnow
from app.core.errors import ConflictError, NotFoundError
from app.engine.runner import ExperimentRunner
from app.engine.state_manager import StateManager
from app.models.experiment import ExperimentStatus as S
from app.proxy.rules import RuleRegistry
from app.storage.database import session_scope
from app.storage.repositories import ExperimentRepository

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, runner: ExperimentRunner, registry: RuleRegistry, state: StateManager):
        self._runner, self._registry, self._state = runner, registry, state

    @property
    def active_count(self) -> int:
        return self._state.active_count()

    def start(self, experiment_id: str) -> None:
        self._ensure_startable(experiment_id)
        self._state.register(experiment_id, asyncio.create_task(self._runner.run(experiment_id)))

    def start_suite(self, suite_id: str, experiment_ids: list[str]) -> None:
        if self._state.is_busy():
            raise ConflictError("Another experiment is already running")
        self._state.start_suite(suite_id, experiment_ids)
        self._state.register(suite_id, asyncio.create_task(self._run_suite(suite_id, experiment_ids)))

    async def stop(self, experiment_id: str) -> None:
        """Kill switch: clear fault rules first, then cancel the task, then persist state."""
        self._registry.deactivate(experiment_id)
        suite_id = self._state.suite_of(experiment_id)
        if suite_id:
            self._state.suite(suite_id)["stop"] = True
        task = self._state.task_for(experiment_id)
        if task:
            task.cancel()
            await asyncio.wait({task}, timeout=5)
        else:
            self._mark_stopped(experiment_id, "Stopped before it started")

    async def stop_suite(self, suite_id: str) -> None:
        suite = self._state.suite(suite_id)
        if not suite:
            raise NotFoundError("Suite is not running")
        suite["stop"] = True
        if suite["current"]:
            await self.stop(suite["current"])

    async def shutdown(self) -> None:
        self._registry.clear_all()
        for task in list(self._state._tasks.values()):
            task.cancel()

    # ---- internals --------------------------------------------------------------------------
    async def _run_suite(self, suite_id: str, experiment_ids: list[str]) -> None:
        suite = self._state.suite(suite_id)
        try:
            for experiment_id in experiment_ids:
                if suite["stop"]:
                    self._mark_stopped(experiment_id, "Skipped: suite stopped")
                    continue
                suite["current"] = experiment_id
                task = asyncio.create_task(self._runner.run(experiment_id))
                self._state.register(experiment_id, task)
                try:
                    await asyncio.wait({task})
                except asyncio.CancelledError:
                    task.cancel()
                    raise
                if task.cancelled():
                    suite["stop"] = True
        except asyncio.CancelledError:
            for experiment_id in experiment_ids:
                self._mark_stopped(experiment_id, "Skipped: suite cancelled")
            raise
        finally:
            self._state.end_suite(suite_id)

    def _ensure_startable(self, experiment_id: str) -> None:
        with session_scope() as session:
            exp = ExperimentRepository(session).get(experiment_id)
        if exp is None:
            raise NotFoundError(f"Experiment {experiment_id} not found")
        if exp.status != S.CREATED.value:
            raise ConflictError(f"Experiment is {exp.status}; only CREATED experiments can start")
        if self._state.is_busy():
            raise ConflictError("Another experiment is already running")

    def _mark_stopped(self, experiment_id: str, message: str) -> None:
        with session_scope() as session:
            repo = ExperimentRepository(session)
            exp = repo.get(experiment_id)
            if exp and exp.status == S.CREATED.value:
                exp.status, exp.error_message, exp.completed_at = S.STOPPED.value, message, utcnow()
                repo.save(exp)
