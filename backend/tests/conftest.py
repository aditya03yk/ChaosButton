"""Shared fixtures: an in-process fake target and a mocked AI provider at the test boundary."""
import time

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai.provider import AIProvider, AIUnavailableError
from app.ai.schemas import AIStatus, AnalysisResult, CodeExample, FixValidation, Severity
from app.core.config import Settings
from app.main import create_app

TERMINAL = {"COMPLETED", "STOPPED", "FAILED"}


def make_fake_target() -> FastAPI:
    target = FastAPI()

    @target.get("/health")
    def health():
        return {"status": "ok"}

    @target.get("/product")
    def product():
        return {"name": "widget"}

    return target


class FakeAI(AIProvider):
    """Stands in for Gemma in tests only; the real provider is OllamaGemmaProvider."""
    model_name = "fake-gemma"

    async def status(self):
        return AIStatus(provider="fake", model="fake-gemma", reachable=True, model_available=True, message="ok")

    async def generate_analysis(self, evidence: dict) -> AnalysisResult:
        return AnalysisResult(
            finding="Dependency failures are not handled", severity=Severity.HIGH,
            severity_rationale="Error rate was 100% in the fault period",
            evidence=[f"requests={evidence['measured']['fault_period_requests']}"],
            likely_cause="The route may lack a fallback", recommended_actions=["Add a fallback"],
            code_example=CodeExample(language="python", snippet="timeout=0.5", assumptions="httpx"),
            verification_steps=["Rerun the same experiment"])

    async def generate_fix_validation(self, comparison: dict) -> FixValidation:
        return FixValidation(summary="Error rate improved", improvements=["error_rate"])


class UnavailableAI(FakeAI):
    async def generate_analysis(self, evidence):
        raise AIUnavailableError("Ollama is not reachable. Start it with `ollama serve` and retry.")


def build_client(tmp_path, ai: AIProvider):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", recovery_probe_count=4,
                        recovery_probe_interval_ms=5)
    http = httpx.AsyncClient(transport=httpx.ASGITransport(app=make_fake_target()))
    return TestClient(create_app(settings, http, ai))


@pytest.fixture
def client(tmp_path):
    with build_client(tmp_path, FakeAI()) as c:
        yield c


@pytest.fixture
def client_no_ai(tmp_path):
    with build_client(tmp_path, UnavailableAI()) as c:
        yield c


@pytest.fixture
def target_id(client):
    response = client.post("/api/targets", json={"name": "Fake shop", "base_url": "http://127.0.0.1:9001",
                                                 "environment_type": "demo"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def wait_for(client, experiment_id: str, states: set, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/experiments/{experiment_id}").json()
        if body["status"] in states:
            return body
        time.sleep(0.05)
    raise AssertionError(f"experiment stuck in {body['status']}")


def experiment_payload(target_id: int, fault_type="http_503", **fault) -> dict:
    config = {"max_affected": 4, "baseline_requests": 3, "interval_ms": 0, "duration_s": 10, **fault}
    return {"target_id": target_id, "route": "/product", "fault_type": fault_type, "fault_configuration": config}


def run_experiment(client, target_id: int, fault_type="http_503", **fault) -> dict:
    created = client.post("/api/experiments", json=experiment_payload(target_id, fault_type, **fault)).json()
    assert client.post(f"/api/experiments/{created['id']}/start").status_code == 202
    return wait_for(client, created["id"], TERMINAL)
