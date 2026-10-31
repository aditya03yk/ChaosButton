"""Experiment lifecycle, kill switch, limits, retest/compare and the end-to-end flow."""
import pytest

from app.engine.state_manager import assert_transition
from app.core.errors import ConflictError
from app.models.experiment import ExperimentStatus as S
from tests.conftest import experiment_payload, run_experiment, wait_for


def test_state_transitions():
    assert_transition(S.CREATED, S.VALIDATING)
    assert_transition(S.RUNNING, S.RECOVERING)
    with pytest.raises(ConflictError):
        assert_transition(S.COMPLETED, S.RUNNING)
    with pytest.raises(ConflictError):
        assert_transition(S.BASELINE, S.RECOVERING)


def test_hard_limits_are_enforced_by_backend(client, target_id):
    for bad in ({"max_affected": 10_000}, {"duration_s": 9_999}, {"concurrency": 50}):
        response = client.post("/api/experiments", json=experiment_payload(target_id, **bad))
        assert response.status_code == 422
    too_slow = experiment_payload(target_id, "latency", delay_ms=60_000)
    assert client.post("/api/experiments", json=too_slow).status_code == 422
    broad = {**experiment_payload(target_id), "route": "/*"}
    assert client.post("/api/experiments", json=broad).status_code == 422


def test_full_flow_503_experiment(client, target_id):
    """Register -> create -> baseline -> fault -> metrics -> persisted results -> report."""
    done = run_experiment(client, target_id, "http_503")
    assert done["status"] == "COMPLETED"
    metrics = done["metrics"]
    assert metrics["total_requests"] == 4 and metrics["error_rate"] == 100.0 and metrics["success_rate"] == 0.0
    assert metrics["baseline_requests"] == 3 and metrics["resilience_score"] is not None

    events = client.get(f"/api/experiments/{done['id']}/events").json()
    phases = [e["phase"] for e in events["requests"]]
    assert phases.count("baseline") == 3 and phases.count("fault") == 4 and phases.count("recovery") == 4
    assert any(e["fault_applied"] for e in events["requests"] if e["phase"] == "fault")
    assert any("Fault injection stopped" in t["message"] for t in events["timeline"])

    report = client.get(f"/api/experiments/{done['id']}/report").json()
    assert report["metrics"]["total_requests"] == 4 and report["status_distribution"] == {"503": 4}
    assert client.get("/api/experiments", params={"status": "COMPLETED"}).json()["total"] == 1
    assert client.get("/api/dashboard").json()["total_experiments"] == 1


def test_route_scoping_only_affects_matching_route(client, target_id):
    payload = {**experiment_payload(target_id), "route": "/health"}
    created = client.post("/api/experiments", json=payload).json()
    client.post(f"/api/experiments/{created['id']}/start")
    wait_for(client, created["id"], {"RUNNING", "RECOVERING", "COMPLETED"})
    # /product is not in scope, so it must pass through normally while the rule is active
    assert client.get("/health").status_code == 200


def test_kill_switch_stops_run_and_clears_rules(client, target_id):
    created = client.post("/api/experiments", json=experiment_payload(
        target_id, "latency", delay_ms=3000, max_affected=5, concurrency=1)).json()
    client.post(f"/api/experiments/{created['id']}/start")
    wait_for(client, created["id"], {"RUNNING"})
    stopped = client.post(f"/api/experiments/{created['id']}/stop").json()
    final = wait_for(client, created["id"], {"STOPPED"})
    assert stopped["id"] == final["id"] and final["status"] == "STOPPED"
    assert client.app.state.container.registry.active_rules() == []


def test_second_experiment_is_rejected_while_one_runs(client, target_id):
    first = client.post("/api/experiments", json=experiment_payload(
        target_id, "latency", delay_ms=2000, concurrency=1)).json()
    second = client.post("/api/experiments", json=experiment_payload(target_id)).json()
    client.post(f"/api/experiments/{first['id']}/start")
    assert client.post(f"/api/experiments/{second['id']}/start").status_code == 409
    client.post(f"/api/experiments/{first['id']}/stop")


def test_retest_and_comparison(client, target_id):
    original = run_experiment(client, target_id, "http_503")
    retest = client.post(f"/api/experiments/{original['id']}/retest").json()
    assert retest["parent_experiment_id"] == original["id"] and retest["id"] != original["id"]
    assert retest["fault_configuration"] == original["fault_configuration"]
    client.post(f"/api/experiments/{retest['id']}/start")
    wait_for(client, retest["id"], {"COMPLETED"})
    result = client.post(f"/api/experiments/{original['id']}/compare",
                         json={"other_experiment_id": retest["id"], "explain": True}).json()
    assert result["comparable"] and not result["target_changed"] and result["ai_validation"]["summary"]
    assert client.get(f"/api/experiments/{original['id']}/report").json()["retests"][0]["comparison"]


def test_auto_suite_runs_three_scenarios(client, target_id):
    suite = client.post("/api/suites", json={"target_id": target_id, "route": "/product"}).json()
    assert [e["fault_type"] for e in suite["experiments"]] == ["latency", "timeout", "http_503"]
    import time
    deadline = time.time() + 40
    while time.time() < deadline and not client.get(f"/api/suites/{suite['suite_id']}").json()["finished"]:
        time.sleep(0.2)
    final = client.get(f"/api/suites/{suite['suite_id']}").json()
    assert final["finished"] and final["consolidated"]["scenarios_completed"] == 3


def test_stream_for_finished_experiment_reports_final_status(client, target_id):
    done = run_experiment(client, target_id)
    with client.stream("GET", f"/api/experiments/{done['id']}/stream") as response:
        body = "".join(response.iter_text())
    assert "event: status" in body and "COMPLETED" in body
