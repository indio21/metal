from io import BytesIO
from pathlib import Path
import shutil

from app import create_app
from app.models import Project, Template, UploadedModel


def reset_test_upload_dirs(app):
    for folder_key in ("UPLOAD_FOLDER", "EXPORT_FOLDER"):
        folder = Path(app.config[folder_key])
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)


def test_dashboard_route():
    app = create_app("testing")
    reset_test_upload_dirs(app)
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Metal MVP" in response.data


def test_projects_index_route():
    app = create_app("testing")
    reset_test_upload_dirs(app)
    client = app.test_client()

    response = client.get("/projects")

    assert response.status_code == 200
    assert b"Listado de proyectos" in response.data


def test_new_project_route():
    app = create_app("testing")
    reset_test_upload_dirs(app)
    client = app.test_client()

    response = client.get("/projects/new")

    assert response.status_code == 200
    assert b"Nueva pieza" in response.data


def test_create_project_persists_and_redirects_to_detail():
    app = create_app("testing")
    reset_test_upload_dirs(app)
    client = app.test_client()

    response = client.post(
        "/projects/new",
        data={
            "name": "Soporte principal",
            "part_number": "SOP-001",
            "revision": "B",
            "material": "Acero SAE 1010",
            "author": "Pablo",
            "template_id": "",
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
        assert project.revision == "B"
        assert project.author == "Pablo"


def test_default_template_is_seeded():
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        template = Template.query.filter_by(code="industrial-a4").first()
        assert template is not None


def test_edit_project_updates_fields():
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        template = Template.query.filter_by(code="industrial-a4").first()
        project = Project(name="Brida original", revision="A", status="draft")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        project_id = project.id
        template_id = template.id

    client = app.test_client()
    response = client.post(
        f"/projects/{project_id}/edit",
        data={
            "name": "Brida revisada",
            "part_number": "BRI-200",
            "revision": "C",
            "material": "Acero inoxidable",
            "author": "Equipo CAD",
            "template_id": str(template_id),
            "status": "ready",
            "notes": "Lista para la siguiente fase.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Proyecto actualizado correctamente." in response.data
    assert b"Brida revisada" in response.data

    with app.app_context():
        project = app.extensions["sqlalchemy"].session.get(Project, project_id)
        assert project is not None
        assert project.revision == "C"
        assert project.author == "Equipo CAD"
        assert project.template_id == template_id


def test_delete_project_removes_record():
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        project = Project(name="Eliminar pieza", revision="A", status="draft")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        project_id = project.id

    client = app.test_client()
    response = client.post(f"/projects/{project_id}/delete", follow_redirects=True)

    assert response.status_code == 200
    assert b"eliminado correctamente" in response.data

    with app.app_context():
        project = app.extensions["sqlalchemy"].session.get(Project, project_id)
        assert project is None


def test_missing_project_shows_friendly_404():
    app = create_app("testing")
    reset_test_upload_dirs(app)
    client = app.test_client()

    response = client.get("/projects/9999")

    assert response.status_code == 404
    assert b"No encontramos lo que buscabas" in response.data


def test_upload_valid_step_file_persists_metadata_and_file():
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        project = Project(name="Pieza con CAD", revision="A", status="draft")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        project_id = project.id

    client = app.test_client()
    response = client.post(
        f"/projects/{project_id}/upload-model",
        data={"cad_file": (BytesIO(b"dummy step data"), "pieza.step")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Archivo CAD asociado correctamente al proyecto." in response.data
    assert b"pieza.step" in response.data

    with app.app_context():
        uploaded_model = UploadedModel.query.filter_by(project_id=project_id).first()
        assert uploaded_model is not None
        assert uploaded_model.file_format == "step"
        stored_path = Path(app.config["UPLOAD_FOLDER"]) / uploaded_model.storage_path
        assert stored_path.exists()


def test_upload_rejects_invalid_extension():
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        project = Project(name="Pieza invalida", revision="A", status="draft")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        project_id = project.id

    client = app.test_client()
    response = client.post(
        f"/projects/{project_id}/upload-model",
        data={"cad_file": (BytesIO(b"dummy pdf"), "plano.pdf")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Formato no soportado" in response.data

    with app.app_context():
        uploaded_models = UploadedModel.query.filter_by(project_id=project_id).all()
        assert uploaded_models == []


def test_download_uploaded_model_returns_file():
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        project = Project(name="Pieza descarga", revision="A", status="draft")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        project_id = project.id

    client = app.test_client()
    client.post(
        f"/projects/{project_id}/upload-model",
        data={"cad_file": (BytesIO(b"iges-data"), "pieza.iges")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        uploaded_model = UploadedModel.query.filter_by(project_id=project_id).first()
        model_id = uploaded_model.id

    response = client.get(f"/projects/{project_id}/models/{model_id}/download")

    assert response.status_code == 200
    assert response.data == b"iges-data"
