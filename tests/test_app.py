from app import create_app
from app.models import Project, Template


def test_dashboard_route():
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Metal MVP" in response.data


def test_projects_index_route():
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/projects")

    assert response.status_code == 200
    assert b"Listado de proyectos" in response.data


def test_new_project_route():
    app = create_app("testing")
    client = app.test_client()

    response = client.get("/projects/new")

    assert response.status_code == 200
    assert b"Crear proyecto" in response.data


def test_create_project_persists_and_redirects_to_detail():
    app = create_app("testing")
    client = app.test_client()

    response = client.post(
        "/projects/new",
        data={
            "name": "Soporte principal",
            "part_number": "SOP-001",
            "material": "Acero SAE 1010",
            "status": "draft",
            "notes": "Proyecto inicial para pruebas.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Proyecto creado correctamente." in response.data
    assert b"Soporte principal" in response.data

    with app.app_context():
        project = Project.query.filter_by(name="Soporte principal").first()
        assert project is not None
        assert project.part_number == "SOP-001"


def test_default_template_is_seeded():
    app = create_app("testing")

    with app.app_context():
        template = Template.query.filter_by(code="industrial-a4").first()
        assert template is not None
