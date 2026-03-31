from app import create_app


def test_dashboard_route():
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Metal MVP" in response.data


def test_new_project_route():
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/projects/new")

    assert response.status_code == 200
    assert b"Crear proyecto" in response.data
