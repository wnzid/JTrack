from conftest import login_as


def test_api_requires_authentication(client):
    response = client.get("/api/application-status")
    assert response.status_code == 401
    assert response.json["error"]["code"] == "unauthorized"


def test_report_api_enforces_role_and_returns_contract(client):
    login_as(client, "Leader")
    forbidden = client.get("/api/current-vs-enrolled")
    assert forbidden.status_code == 403

    response = client.get("/api/application-status")
    assert response.status_code == 200
    assert isinstance(response.json["data"], list)
    assert response.json["meta"]["report"] == "application-status"
    assert response.json["meta"]["source"] == "sqlite"
    assert response.json["meta"]["count"] > 0


def test_raw_data_is_paginated_and_bounded(client):
    login_as(client, "Manager")
    response = client.get("/api/data?per_page=2&page=2")
    assert response.status_code == 200
    assert len(response.json["data"]) == 2
    assert response.json["meta"]["page"] == 2
    assert response.json["meta"]["total"] == 4
    assert "status" in response.json["meta"]["columns"]


def test_legacy_array_mode_remains_available(client):
    login_as(client, "Manager")
    response = client.get("/api/visa-breakdown?legacy=1")
    assert response.status_code == 200
    assert isinstance(response.json, list)
