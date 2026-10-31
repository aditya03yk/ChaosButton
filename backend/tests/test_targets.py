"""Target API: CRUD, validation and safety rejections."""


def test_create_list_get_update_delete(client):
    created = client.post("/api/targets", json={"name": "Shop", "base_url": "http://127.0.0.1:9001/"})
    assert created.status_code == 201 and created.json()["base_url"] == "http://127.0.0.1:9001"
    tid = created.json()["id"]
    assert [t["id"] for t in client.get("/api/targets").json()] == [tid]
    assert client.patch(f"/api/targets/{tid}", json={"name": "Renamed"}).json()["name"] == "Renamed"
    assert client.delete(f"/api/targets/{tid}").status_code == 204
    assert client.get(f"/api/targets/{tid}").status_code == 404


def test_rejects_unsafe_targets(client):
    assert client.post("/api/targets", json={"name": "x", "base_url": "ftp://127.0.0.1"}).status_code == 422
    remote = client.post("/api/targets", json={"name": "x", "base_url": "http://example.com",
                                                "environment_type": "staging"})
    assert remote.status_code == 422
    assert client.post("/api/targets", json={"name": "", "base_url": "http://127.0.0.1"}).status_code == 422


def test_validate_endpoint_reports_reachability(client):
    ok = client.post("/api/targets/validate", json={"base_url": "http://127.0.0.1:9001"}).json()
    assert ok["valid"] and ok["reachable"] and ok["status_code"] == 200
    bad = client.post("/api/targets/validate", json={"base_url": "http://169.254.169.254"}).json()
    assert not bad["valid"] and bad["errors"]


def test_target_with_history_cannot_be_deleted(client, target_id):
    from tests.conftest import run_experiment
    run_experiment(client, target_id)
    assert client.delete(f"/api/targets/{target_id}").status_code == 409
