from sqlalchemy.exc import SQLAlchemyError

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Project
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

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")

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
    return render_template("projects/detail.html", project=project)


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
