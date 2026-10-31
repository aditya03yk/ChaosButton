"""Fault rule lifecycle: activation, expiry, request caps and the registry."""
import time
from dataclasses import dataclass, field
from typing import Optional

from app.proxy.route_matcher import matches, method_matches


@dataclass
class FaultRule:
    experiment_id: str
    target_id: int
    scope: str
    route: str
    method: str
    fault_type: str
    max_affected: int
    expires_at: float
    delay_ms: Optional[int] = None
    timeout_ms: Optional[int] = None
    status_code: Optional[int] = None
    activated_at: float = field(default_factory=time.time)
    active: bool = True
    # Request ids already affected: retries of an affected request stay affected,
    # so the cap counts distinct client requests, not upstream attempts.
    affected_ids: set = field(default_factory=set)

    @property
    def affected_count(self) -> int:
        return len(self.affected_ids)

    def is_expired(self, now: float) -> bool:
        return now >= self.expires_at

    def try_claim(self, request_id: str) -> bool:
        if request_id in self.affected_ids:
            return True
        if self.affected_count >= self.max_affected:
            return False
        self.affected_ids.add(request_id)
        return True


class RuleRegistry:
    """In-memory registry. Rules live only as long as the process and their expiry."""

    def __init__(self) -> None:
        self._rules: dict[str, FaultRule] = {}

    def activate(self, rule: FaultRule) -> None:
        self._rules[rule.experiment_id] = rule

    def deactivate(self, experiment_id: str) -> None:
        rule = self._rules.pop(experiment_id, None)
        if rule:
            rule.active = False

    def clear_all(self) -> None:
        for experiment_id in list(self._rules):
            self.deactivate(experiment_id)

    def active_rules(self) -> list[FaultRule]:
        self._sweep(time.time())
        return list(self._rules.values())

    def was_affected(self, experiment_id: str, request_id: str) -> bool:
        rule = self._rules.get(experiment_id)
        return bool(rule and request_id in rule.affected_ids)

    def find(self, *, scope: str, target_id: Optional[int], method: str, path: str,
             request_id: str, now: Optional[float] = None) -> Optional[FaultRule]:
        """Return the rule to apply to this request, or None to forward normally."""
        now = time.time() if now is None else now
        self._sweep(now)
        for rule in self._rules.values():
            if rule.scope != scope or (scope == "inbound" and rule.target_id != target_id):
                continue
            if matches(rule.route, path) and method_matches(rule.method, method) and rule.try_claim(request_id):
                return rule
        return None

    def _sweep(self, now: float) -> None:
        for experiment_id, rule in list(self._rules.items()):
            if rule.is_expired(now):
                self.deactivate(experiment_id)
