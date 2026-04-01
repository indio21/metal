from io import BytesIO
import json
from pathlib import Path
import shutil

from app import create_app
from app.models import DrawingJob, ExportFile, Project, Template, UploadedModel


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


def test_analyze_uploaded_model_success(monkeypatch):
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        project = Project(name="Pieza analizada", revision="A", status="draft")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        project_id = project.id

    client = app.test_client()
    client.post(
        f"/projects/{project_id}/upload-model",
        data={"cad_file": (BytesIO(b"step-data"), "pieza.step")},
        content_type="multipart/form-data",
    )

    def fake_analyze_model(self, file_path):
        from app.cad.cad_import_service import CADAnalysisResult

        return CADAnalysisResult(
            backend="FreeCAD",
            bounding_box={
                "xmin": 0.0,
                "ymin": 0.0,
                "zmin": 0.0,
                "xmax": 120.0,
                "ymax": 45.0,
                "zmax": 30.0,
            },
            dimensions={"x": 120.0, "y": 45.0, "z": 30.0},
            tentative_scale_factor=1.0,
            tentative_scale_note="Escala base del archivo.",
        )

    monkeypatch.setattr(
        "app.cad.cad_import_service.FreeCADAdapter.analyze_model",
        fake_analyze_model,
    )

    with app.app_context():
        uploaded_model = UploadedModel.query.filter_by(project_id=project_id).first()
        model_id = uploaded_model.id

    response = client.post(
        f"/projects/{project_id}/analyze-model",
        data={"model_id": str(model_id)},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Analisis del modelo completado correctamente." in response.data
    assert b"Dimension X" in response.data
    assert b"120.0" in response.data

    with app.app_context():
        drawing_job = DrawingJob.query.filter_by(project_id=project_id, output_type="model_analysis").first()
        project = app.extensions["sqlalchemy"].session.get(Project, project_id)
        assert drawing_job is not None
        assert drawing_job.status == "completed"
        assert project.status == "ready"


def test_analyze_uploaded_model_handles_freecad_unavailable(monkeypatch):
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        project = Project(name="Pieza sin FreeCAD", revision="A", status="draft")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        project_id = project.id

    client = app.test_client()
    client.post(
        f"/projects/{project_id}/upload-model",
        data={"cad_file": (BytesIO(b"iges-data"), "pieza.iges")},
        content_type="multipart/form-data",
    )

    from app.cad.cad_import_service import FreeCADUnavailableError

    def fake_fail(self, file_path):
        raise FreeCADUnavailableError("FreeCAD no esta disponible en este entorno.")

    monkeypatch.setattr(
        "app.cad.cad_import_service.FreeCADAdapter.analyze_model",
        fake_fail,
    )

    with app.app_context():
        uploaded_model = UploadedModel.query.filter_by(project_id=project_id).first()
        model_id = uploaded_model.id

    response = client.post(
        f"/projects/{project_id}/analyze-model",
        data={"model_id": str(model_id)},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"no pudo completarse" in response.data
    assert b"FreeCAD no esta disponible en este entorno." in response.data

    with app.app_context():
        drawing_job = DrawingJob.query.filter_by(project_id=project_id, output_type="model_analysis").first()
        assert drawing_job is not None
        assert drawing_job.status == "failed"


def test_generate_preliminary_drawing_creates_svg_preview():
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        project = Project(name="Pieza drawing", revision="A", status="ready")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        uploaded_model = UploadedModel(
            project_id=project.id,
            original_filename="pieza.step",
            stored_filename="pieza.step",
            file_format="step",
            storage_path=f"project_{project.id}/pieza.step",
            status="uploaded",
        )
        app.extensions["sqlalchemy"].session.add(uploaded_model)
        app.extensions["sqlalchemy"].session.commit()
        upload_path = Path(app.config["UPLOAD_FOLDER"]) / uploaded_model.storage_path
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        upload_path.write_bytes(b"step-data")
        analysis_job = DrawingJob(
            project_id=project.id,
            uploaded_model_id=uploaded_model.id,
            status="completed",
            output_type="model_analysis",
            analyzer_backend="FreeCAD",
            analysis_summary=json.dumps(
                {
                    "backend": "FreeCAD",
                    "bounding_box": {
                        "xmin": 0.0,
                        "ymin": 0.0,
                        "zmin": 0.0,
                        "xmax": 140.0,
                        "ymax": 60.0,
                        "zmax": 35.0,
                    },
                    "dimensions": {"x": 140.0, "y": 60.0, "z": 35.0},
                    "tentative_scale_factor": 1.0,
                    "tentative_scale_note": "Escala base del archivo.",
                }
            ),
        )
        app.extensions["sqlalchemy"].session.add(analysis_job)
        app.extensions["sqlalchemy"].session.commit()
        project_id = project.id
        model_id = uploaded_model.id

    client = app.test_client()
    response = client.post(
        f"/projects/{project_id}/generate-drawing",
        data={"model_id": str(model_id)},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Drawing preliminar generado correctamente." in response.data
    assert b"Hoja 2D generada" in response.data
    assert b"Abrir preview" in response.data

    with app.app_context():
        drawing_job = DrawingJob.query.filter_by(project_id=project_id, output_type="preliminary_2d").first()
        assert drawing_job is not None
        assert drawing_job.status == "completed"
        export_file = ExportFile.query.filter_by(drawing_job_id=drawing_job.id, file_format="svg").first()
        assert export_file is not None
        preview_path = Path(app.config["EXPORT_FOLDER"]) / export_file.file_path
        assert preview_path.exists()
        assert "<svg" in preview_path.read_text(encoding="utf-8")


def test_preview_generated_drawing_returns_svg():
    app = create_app("testing")
    reset_test_upload_dirs(app)

    with app.app_context():
        project = Project(name="Pieza preview", revision="A", status="ready")
        app.extensions["sqlalchemy"].session.add(project)
        app.extensions["sqlalchemy"].session.commit()
        drawing_job = DrawingJob(
            project_id=project.id,
            status="completed",
            output_type="preliminary_2d",
            analyzer_backend="svg_fallback",
            analysis_summary=json.dumps({"scale_label": "1:1", "template_name": "Industrial basico A4"}),
        )
        app.extensions["sqlalchemy"].session.add(drawing_job)
        app.extensions["sqlalchemy"].session.commit()
        export_file = ExportFile(
            project_id=project.id,
            drawing_job_id=drawing_job.id,
            filename="preview.svg",
            file_format="svg",
            file_path=f"project_{project.id}/preview.svg",
            status="generated",
        )
        app.extensions["sqlalchemy"].session.add(export_file)
        app.extensions["sqlalchemy"].session.commit()
        preview_path = Path(app.config["EXPORT_FOLDER"]) / export_file.file_path
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        preview_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
        project_id = project.id
        export_id = export_file.id

    client = app.test_client()
    response = client.get(f"/projects/{project_id}/drawings/{export_id}/preview")

    assert response.status_code == 200
    assert response.mimetype == "image/svg+xml"
