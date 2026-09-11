from conftest import login_as


def test_public_pages_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/about").status_code == 200
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "service": "jtrack", "data_source": "sqlite"}


def test_protected_page_redirects_to_login(client):
    response = client.get("/leader-dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_registration_validates_and_creates_session(client):
    with client.session_transaction() as session:
        session["csrf_token"] = "test-csrf"
    short = client.post(
        "/register",
        data={"csrf_token": "test-csrf", "email": "new@example.com", "password": "short", "role": "Leader"},
    )
    assert short.status_code == 200
    assert b"12 characters" in short.data

    created = client.post(
        "/register",
        data={"csrf_token": "test-csrf", "email": "new@example.com", "password": "a-secure-password", "role": "Leader"},
    )
    assert created.status_code == 302
    assert created.headers["Location"].endswith("/welcome")


def test_logout_requires_csrf_and_clears_session(client):
    login_as(client, "Leader")
    assert client.post("/logout").status_code == 400
    response = client.post("/logout", data={"csrf_token": "test-csrf"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
