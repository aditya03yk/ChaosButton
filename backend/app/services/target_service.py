"""Target registration, validation and health probing."""
import time
from typing import Optional

import httpx
from sqlmodel import Session

from app.core.clock import utcnow
from app.core.config import Settings
from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.core.security import check_target_url
from app.models.target import Target, TargetCreate, TargetUpdate, ValidationResult
from app.storage.repositories import TargetRepository


async def validate_url(base_url: str, ownership_confirmed: bool, environment_type: str,
                       settings: Settings, http: httpx.AsyncClient, probe: bool = True) -> ValidationResult:
    """Static safety checks, then (optionally) a safe GET health probe without following redirects."""
    check = await check_target_url(base_url, ownership_confirmed=ownership_confirmed,
                                   environment_type=environment_type, settings=settings)
    result = ValidationResult(valid=check.ok, normalized_url=check.normalized_url,
                              errors=list(check.errors), warnings=list(check.warnings))
    if check.ok and check.loopback and _is_self(check.normalized_url, settings):
        result.valid, result.errors = False, ["The target points at ChaosButton itself."]
    if not (result.valid and probe):
        return result
    for path in ("/health", "/"):
        started = time.perf_counter()
        try:
            response = await http.get(check.normalized_url + path, timeout=3.0, follow_redirects=False)
        except httpx.HTTPError:
            continue
        result.reachable, result.status_code = True, response.status_code
        result.latency_ms = round((time.perf_counter() - started) * 1000, 2)
        if response.status_code < 500:
            break
    if not result.reachable:
        result.valid = False
        result.errors.append("The target is not reachable. Is the application running?")
    elif result.status_code and result.status_code >= 500:
        result.warnings.append(f"The health check returned HTTP {result.status_code}.")
    elif result.status_code and 300 <= result.status_code < 400:
        result.warnings.append("The target redirects; redirects are never followed by ChaosButton.")
    return result


def _is_self(url: str, settings: Settings) -> bool:
    return url.rstrip("/").endswith(f":{settings.app_port}")


class TargetService:
    def __init__(self, session: Session, settings: Settings, http: httpx.AsyncClient):
        self._repo, self._settings, self._http = TargetRepository(session), settings, http

    def get(self, target_id: int) -> Target:
        target = self._repo.get(target_id)
        if target is None:
            raise NotFoundError(f"Target {target_id} not found")
        return target

    def list(self) -> list[Target]:
        return list(self._repo.list())

    async def create(self, data: TargetCreate) -> Target:
        result = await validate_url(data.base_url, data.ownership_confirmed, data.environment_type.value,
                                    self._settings, self._http, probe=False)
        if not result.valid:
            raise UnprocessableError(" ".join(result.errors))
        fields = data.model_dump(mode="json")
        return self._repo.save(Target(**{**fields, "base_url": result.normalized_url}))

    async def update(self, target_id: int, data: TargetUpdate) -> Target:
        target = self.get(target_id)
        for key, value in data.model_dump(exclude_unset=True, mode="json").items():
            setattr(target, key, value)
        result = await validate_url(target.base_url, target.ownership_confirmed, target.environment_type,
                                    self._settings, self._http, probe=False)
        if not result.valid:
            raise UnprocessableError(" ".join(result.errors))
        target.base_url, target.updated_at = result.normalized_url, utcnow()
        target.last_validated_at, target.last_validation_ok = None, None
        return self._repo.save(target)

    def delete(self, target_id: int) -> None:
        target = self.get(target_id)
        if self._repo.has_experiments(target_id):
            raise ConflictError("This target has experiment history and cannot be removed.")
        self._repo.delete(target)

    async def revalidate(self, target_id: int) -> ValidationResult:
        target = self.get(target_id)
        result = await validate_url(target.base_url, target.ownership_confirmed, target.environment_type,
                                    self._settings, self._http)
        target.last_validated_at, target.last_validation_ok = utcnow(), result.valid
        self._repo.save(target)
        return result
