from flask import Blueprint, render_template

from app.models import Project

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def dashboard():
    project_count = Project.query.count()
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        project_count=project_count,
        recent_projects=recent_projects,
    )
