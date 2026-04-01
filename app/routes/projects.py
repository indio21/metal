from sqlalchemy.exc import SQLAlchemyError

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, session, url_for

from app.ai.ollama_service import get_ollama_runtime_status, request_project_assistance
from app.cad.cad_import_service import analyze_project_model
from app.cad.techdraw_service import DrawingGenerationError, generate_preliminary_drawing, resolve_export_path
from app.extensions import db
from app.models import DrawingJob, ExportFile, Project, UploadedModel
from app.services.export_service import (
    ExportDependencyError,
    ExportGenerationError,
    generate_export_file,
    resolve_generated_export_path,
)
from app.services.project_service import (
    PROJECT_STATUS_OPTIONS,
    build_project_form_data,
    create_project,
    delete_project,
    list_active_templates,
    list_projects,
    rollback_session,
    update_project,
    validate_project_form,
)
from app.services.upload_service import (
    UploadStorageError,
    UploadValidationError,
    handle_model_upload,
    resolve_uploaded_model_path,
)

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")
PROJECT_AI_RESULT_KEY = "project_ai_result"

@projects_bp.get("")
def index():
    projects = list_projects()
    return render_template("projects/index.html", projects=projects)


@projects_bp.route("/new", methods=["GET", "POST"])
def new_project():
    form_data = build_project_form_data()
    errors: dict[str, str] = {}
    templates = list_active_templates()

    if request.method == "POST":
        form_data = build_project_form_data(request.form)
        errors = validate_project_form(form_data, templates)

        if not errors:
            try:
                project = create_project(form_data)
            except SQLAlchemyError:
                rollback_session()
                flash("No se pudo guardar el proyecto. Intenta nuevamente.", "danger")
            else:
                flash("Proyecto creado correctamente.", "success")
                return redirect(url_for("projects.detail", project_id=project.id))

        flash("Revisa los datos del formulario para continuar.", "danger")

    return render_template(
        "projects/new.html",
        form_data=form_data,
        errors=errors,
        status_options=PROJECT_STATUS_OPTIONS,
        template_options=templates,
        page_mode="create",
    )


@projects_bp.get("/<int:project_id>")
def detail(project_id: int):
    project = db.get_or_404(Project, project_id)
    latest_analysis_job = (
        DrawingJob.query.filter_by(project_id=project.id, output_type="model_analysis")
        .order_by(DrawingJob.created_at.desc())
        .first()
    )
    latest_drawing_job = (
        DrawingJob.query.filter_by(project_id=project.id, output_type="preliminary_2d")
        .order_by(DrawingJob.created_at.desc())
        .first()
    )
    export_history = sorted(project.export_files, key=lambda export: export.created_at, reverse=True)
    ai_result = session.get(PROJECT_AI_RESULT_KEY)
    if ai_result and ai_result.get("project_id") != project.id:
        ai_result = None
    return render_template(
        "projects/detail.html",
        project=project,
        latest_analysis_job=latest_analysis_job,
        latest_drawing_job=latest_drawing_job,
        export_history=export_history,
        ai_result=ai_result,
        ollama_status=get_ollama_runtime_status(current_app.config),
    )


@projects_bp.post("/<int:project_id>/upload-model")
def upload_model(project_id: int):
    project = db.get_or_404(Project, project_id)
    cad_file = request.files.get("cad_file")

    try:
        handle_model_upload(
            project=project,
            file_storage=cad_file,
            upload_root=current_app.config["UPLOAD_FOLDER"],
        )
    except UploadValidationError as error:
        flash(str(error), "danger")
    except UploadStorageError as error:
        rollback_session()
        flash(str(error), "danger")
    except SQLAlchemyError:
        rollback_session()
        flash("No se pudo registrar el archivo en la base de datos.", "danger")
    else:
        flash("Archivo CAD asociado correctamente al proyecto.", "success")

    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.post("/<int:project_id>/analyze-model")
def analyze_model(project_id: int):
    project = db.get_or_404(Project, project_id)
    model_id = request.form.get("model_id", type=int)

    if model_id:
        uploaded_model = db.get_or_404(UploadedModel, model_id)
        if uploaded_model.project_id != project.id:
            flash("El archivo seleccionado no pertenece a este proyecto.", "danger")
            return redirect(url_for("projects.detail", project_id=project.id))
    else:
        uploaded_model = (
            UploadedModel.query.filter_by(project_id=project.id)
            .order_by(UploadedModel.created_at.desc())
            .first()
        )

    if uploaded_model is None:
        flash("No hay ningun modelo STEP o IGES disponible para analizar.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    try:
        drawing_job = analyze_project_model(
            project=project,
            uploaded_model=uploaded_model,
            upload_root=current_app.config["UPLOAD_FOLDER"],
            freecad_lib_path=current_app.config.get("FREECAD_LIB_PATH"),
        )
    except SQLAlchemyError:
        rollback_session()
        flash("No se pudo registrar el analisis del modelo.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    if drawing_job.status == "completed":
        if drawing_job.analysis_data.get("is_demo_fallback"):
            flash(
                "Analisis completado en modo demo. Se estimaron dimensiones basicas para continuar sin FreeCAD.",
                "warning",
            )
        else:
            flash("Analisis del modelo completado correctamente.", "success")
    else:
        flash("El analisis del modelo no pudo completarse.", "warning")

    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.post("/<int:project_id>/generate-drawing")
def generate_drawing(project_id: int):
    project = db.get_or_404(Project, project_id)
    model_id = request.form.get("model_id", type=int)

    if model_id:
        uploaded_model = db.get_or_404(UploadedModel, model_id)
        if uploaded_model.project_id != project.id:
            flash("El archivo seleccionado no pertenece a este proyecto.", "danger")
            return redirect(url_for("projects.detail", project_id=project.id))
    else:
        uploaded_model = (
            UploadedModel.query.filter_by(project_id=project.id)
            .order_by(UploadedModel.created_at.desc())
            .first()
        )

    if uploaded_model is None:
        flash("Debes subir un archivo STEP o IGES antes de generar el drawing.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    try:
        drawing_job = generate_preliminary_drawing(
            project=project,
            uploaded_model=uploaded_model,
            export_root=current_app.config["EXPORT_FOLDER"],
            upload_root=current_app.config["UPLOAD_FOLDER"],
            freecad_lib_path=current_app.config.get("FREECAD_LIB_PATH"),
        )
    except SQLAlchemyError:
        rollback_session()
        flash("No se pudo registrar la generacion del drawing.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    if drawing_job.status == "completed":
        flash("Drawing preliminar generado correctamente.", "success")
    else:
        flash("No se pudo generar el drawing preliminar.", "warning")

    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.post("/<int:project_id>/drawings/<int:drawing_job_id>/export")
def export_drawing(project_id: int, drawing_job_id: int):
    project = db.get_or_404(Project, project_id)
    drawing_job = db.get_or_404(DrawingJob, drawing_job_id)
    export_format = (request.form.get("export_format") or "").strip().lower()

    if drawing_job.project_id != project.id:
        flash("El drawing seleccionado no pertenece a este proyecto.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    try:
        export_file = generate_export_file(
            project=project,
            drawing_job=drawing_job,
            export_root=current_app.config["EXPORT_FOLDER"],
            target_format=export_format,
        )
    except ExportDependencyError as error:
        flash(str(error), "warning")
    except ExportGenerationError as error:
        flash(str(error), "danger")
    except SQLAlchemyError:
        rollback_session()
        flash("No se pudo registrar la exportacion del drawing.", "danger")
    else:
        flash(
            f"Exportacion {export_file.file_format.upper()} generada correctamente.",
            "success",
        )

    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.post("/<int:project_id>/ai-assist")
def ai_assist(project_id: int):
    project = db.get_or_404(Project, project_id)
    action = (request.form.get("assistant_action") or "").strip()
    latest_drawing_job = (
        DrawingJob.query.filter_by(project_id=project.id, output_type="preliminary_2d")
        .order_by(DrawingJob.created_at.desc())
        .first()
    )
    export_history = sorted(project.export_files, key=lambda export: export.created_at, reverse=True)
    assistance = request_project_assistance(
        project=project,
        action=action,
        config=current_app.config,
        latest_drawing_job=latest_drawing_job,
        export_history=export_history,
    )
    session[PROJECT_AI_RESULT_KEY] = {
        "project_id": project.id,
        "title": assistance.title,
        "content": assistance.content,
        "backend": assistance.backend,
        "used_fallback": assistance.used_fallback,
        "notice": assistance.notice,
    }

    if assistance.used_fallback:
        flash("Asistencia local mostrada porque Ollama no esta disponible.", "warning")
    else:
        flash("Asistencia IA generada correctamente.", "success")

    return redirect(url_for("projects.detail", project_id=project.id))


@projects_bp.route("/<int:project_id>/edit", methods=["GET", "POST"])
def edit(project_id: int):
    project = db.get_or_404(Project, project_id)
    form_data = build_project_form_data(project=project)
    errors: dict[str, str] = {}
    templates = list_active_templates()

    if request.method == "POST":
        form_data = build_project_form_data(request.form)
        errors = validate_project_form(form_data, templates)

        if not errors:
            try:
                update_project(project, form_data)
            except SQLAlchemyError:
                rollback_session()
                flash("No se pudo actualizar el proyecto. Intenta nuevamente.", "danger")
            else:
                flash("Proyecto actualizado correctamente.", "success")
                return redirect(url_for("projects.detail", project_id=project.id))

        flash("Revisa los datos del formulario para continuar.", "danger")

    return render_template(
        "projects/edit.html",
        project=project,
        form_data=form_data,
        errors=errors,
        status_options=PROJECT_STATUS_OPTIONS,
        template_options=templates,
        page_mode="edit",
    )


@projects_bp.post("/<int:project_id>/delete")
def delete(project_id: int):
    project = db.get_or_404(Project, project_id)
    project_name = project.name

    try:
        delete_project(project)
    except SQLAlchemyError:
        rollback_session()
        flash("No se pudo eliminar el proyecto. Intenta nuevamente.", "danger")
        return redirect(url_for("projects.detail", project_id=project_id))

    flash(f'Proyecto "{project_name}" eliminado correctamente.', "success")
    return redirect(url_for("projects.index"))


@projects_bp.get("/<int:project_id>/models/<int:model_id>/download")
def download_model(project_id: int, model_id: int):
    project = db.get_or_404(Project, project_id)
    uploaded_model = db.get_or_404(UploadedModel, model_id)

    if uploaded_model.project_id != project.id:
        flash("El archivo solicitado no pertenece a este proyecto.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    try:
        file_path = resolve_uploaded_model_path(
            current_app.config["UPLOAD_FOLDER"],
            uploaded_model,
        )
    except UploadStorageError as error:
        flash(str(error), "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    return send_file(
        file_path,
        as_attachment=True,
        download_name=uploaded_model.original_filename or uploaded_model.stored_filename,
    )


@projects_bp.get("/<int:project_id>/drawings/<int:export_id>/preview")
def preview_drawing(project_id: int, export_id: int):
    project = db.get_or_404(Project, project_id)
    export_file = db.get_or_404(ExportFile, export_id)

    if export_file.project_id != project.id:
        flash("El drawing solicitado no pertenece a este proyecto.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    try:
        file_path = resolve_export_path(current_app.config["EXPORT_FOLDER"], export_file)
    except DrawingGenerationError as error:
        flash(str(error), "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    return send_file(file_path, mimetype="image/svg+xml")


@projects_bp.get("/<int:project_id>/exports/<int:export_id>/download")
def download_export(project_id: int, export_id: int):
    project = db.get_or_404(Project, project_id)
    export_file = db.get_or_404(ExportFile, export_id)

    if export_file.project_id != project.id:
        flash("La exportacion solicitada no pertenece a este proyecto.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    try:
        file_path = resolve_generated_export_path(current_app.config["EXPORT_FOLDER"], export_file)
    except ExportGenerationError as error:
        flash(str(error), "danger")
        return redirect(url_for("projects.detail", project_id=project.id))

    mimetype = {
        "pdf": "application/pdf",
        "dxf": "application/dxf",
        "svg": "image/svg+xml",
    }.get(export_file.file_format, "application/octet-stream")

    return send_file(
        file_path,
        as_attachment=True,
        download_name=export_file.filename,
        mimetype=mimetype,
    )
