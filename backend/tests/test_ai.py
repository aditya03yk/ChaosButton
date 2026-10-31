"""Gemma provider validation/retry, error states and the fix workflow."""
import asyncio

import pytest

from app.ai.ollama_gemma import OllamaGemmaProvider
from app.ai.provider import AIInvalidOutputError
from app.ai.schemas import AnalysisResult
from app.core.config import Settings
from tests.conftest import run_experiment

VALID = ('{"finding":"Slow dependency","severity":"high","severity_rationale":"p95 grew 10x",'
         '"evidence":["requests=10"],"likely_cause":"No timeout may exist","recommended_actions":["Add timeout"],'
         '"code_example":{"language":"python","snippet":"x=1","assumptions":"httpx"},'
         '"verification_steps":["Rerun"]}')


class ScriptedProvider(OllamaGemmaProvider):
    def __init__(self, replies):
        super().__init__(Settings())
        self.replies, self.calls = list(replies), 0

    async def _chat(self, prompt, schema):
        self.calls += 1
        return self.replies.pop(0)


def test_valid_json_is_parsed():
    result = asyncio.run(ScriptedProvider([VALID])._generate("p", AnalysisResult))
    assert result.finding == "Slow dependency" and result.severity.value == "high"


def test_invalid_output_is_retried_once_then_succeeds():
    provider = ScriptedProvider(["not json", VALID])
    assert asyncio.run(provider._generate("p", AnalysisResult)).severity.value == "high"
    assert provider.calls == 2


def test_persistently_invalid_output_fails_safely():
    provider = ScriptedProvider(['{"finding":"x"}', "{}"])
    with pytest.raises(AIInvalidOutputError):
        asyncio.run(provider._generate("p", AnalysisResult))
    assert provider.calls == 2


def test_status_reports_unreachable_ollama():
    provider = OllamaGemmaProvider(Settings(ollama_base_url="http://127.0.0.1:9"))
    status = asyncio.run(provider.status())
    assert not status.reachable and "ollama serve" in status.hint


def test_analysis_creates_fix_proposal_and_workflow_is_manual(client, target_id):
    done = run_experiment(client, target_id)
    created = client.post(f"/api/experiments/{done['id']}/ai-analysis", json={}).json()
    assert created["analysis"]["severity"] == "high" and created["fix"]["status"] == "proposed"
    fix_id = created["fix"]["id"]
    assert client.patch(f"/api/fixes/{fix_id}", json={"status": "applied"}).status_code == 409  # cannot skip review
    assert client.patch(f"/api/fixes/{fix_id}", json={"status": "reviewed", "developer_notes": "ok"}).status_code == 200
    assert client.patch(f"/api/fixes/{fix_id}", json={"status": "applied"}).json()["status"] == "applied"
    assert len(client.get(f"/api/experiments/{done['id']}/fixes").json()) == 1


def test_analysis_requires_measurements(client, target_id):
    created = client.post("/api/experiments", json={"target_id": target_id, "route": "/product",
                                                    "fault_type": "http_503"}).json()
    assert client.post(f"/api/experiments/{created['id']}/ai-analysis", json={}).status_code == 409


def test_ai_unavailable_is_an_honest_error_not_fake_output(client_no_ai, target_id):
    done = run_experiment(client_no_ai, target_id)
    response = client_no_ai.post(f"/api/experiments/{done['id']}/ai-analysis", json={})
    assert response.status_code == 503 and "ollama serve" in response.json()["detail"]
    assert client_no_ai.get(f"/api/experiments/{done['id']}/fixes").json() == []
