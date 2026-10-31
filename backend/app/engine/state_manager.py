"""Experiment state machine and tracking of running tasks."""
import asyncio
from typing import Optional

from app.core.errors import ConflictError
from app.models.experiment import ExperimentStatus as S

TRANSITIONS: dict[S, set[S]] = {
    S.CREATED: {S.VALIDATING, S.STOPPED, S.FAILED},
    S.VALIDATING: {S.BASELINE, S.STOPPED, S.FAILED},
    S.BASELINE: {S.RUNNING, S.STOPPED, S.FAILED},
    S.RUNNING: {S.RECOVERING, S.STOPPED, S.FAILED},
    S.RECOVERING: {S.COMPLETED, S.STOPPED, S.FAILED},
}


def assert_transition(current: S, new: S) -> None:
    if new not in TRANSITIONS.get(current, set()):
        raise ConflictError(f"Invalid state transition {current.value} -> {new.value}")


class StateManager:
    """Tracks running experiment tasks. Only one experiment may run at a time."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}
        self._suites: dict[str, dict] = {}

    def register(self, key: str, task: asyncio.Task) -> None:
        self._tasks[key] = task
        task.add_done_callback(lambda _t, k=key: self._tasks.pop(k, None))

    def task_for(self, key: str) -> Optional[asyncio.Task]:
        task = self._tasks.get(key)
        return task if task and not task.done() else None

    def active_count(self) -> int:
        return sum(1 for t in self._tasks.values() if not t.done())

    def is_busy(self) -> bool:
        return self.active_count() > 0 or bool(self._suites)

    def start_suite(self, suite_id: str, experiment_ids: list[str]) -> None:
        self._suites[suite_id] = {"ids": experiment_ids, "stop": False, "current": None}

    def suite(self, suite_id: str) -> Optional[dict]:
        return self._suites.get(suite_id)

    def end_suite(self, suite_id: str) -> None:
        self._suites.pop(suite_id, None)

    def suite_of(self, experiment_id: str) -> Optional[str]:
        return next((sid for sid, s in self._suites.items() if s["current"] == experiment_id), None)
