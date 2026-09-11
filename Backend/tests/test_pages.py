import pytest

from conftest import login_as


@pytest.mark.parametrize(
    ("role", "paths"),
    [
        ("Manager", ["/welcome", "/managerial", "/managerial-dashboard", "/custom-dashboard", "/report/current-students", "/report/enrolled-offer", "/report/visa-status", "/report/offer-expiry"]),
        ("Leader", ["/welcome", "/leader-dashboard", "/custom-dashboard", "/report/application-status", "/report/deferred-offers", "/report/agent-performance", "/report/student-classification"]),
    ],
)
def test_role_pages_render(client, role, paths):
    login_as(client, role)
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, path
        assert b"JTrack" in response.data


def test_cross_role_report_is_forbidden(client):
    login_as(client, "Leader")
    assert client.get("/report/visa-status").status_code == 403
