from app.extensions import db
from app.models.mixins import TimestampMixin


class Project(TimestampMixin, db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    project_name = db.Column(db.String(160), nullable=True)
    part_name = db.Column(db.String(160), nullable=True)
    description = db.Column(db.Text, nullable=True)
    part_number = db.Column(db.String(80), nullable=True)
    revision = db.Column(db.String(32), nullable=False, default="A")
    material = db.Column(db.String(80), nullable=True)
    finish = db.Column(db.String(120), nullable=True)
    author = db.Column(db.String(120), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey("templates.id"), nullable=True, index=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="draft")

    template = db.relationship("Template", back_populates="projects")
    uploaded_models = db.relationship(
        "UploadedModel",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    drawing_jobs = db.relationship(
        "DrawingJob",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    export_files = db.relationship(
        "ExportFile",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    STATUS_META = {
        "draft": {"label": "Borrador", "badge": "text-bg-warning"},
        "pending_upload": {"label": "Pendiente de modelo", "badge": "text-bg-secondary"},
        "ready": {"label": "Listo para analisis", "badge": "text-bg-success"},
    }

    @property
    def status_label(self) -> str:
        return self.STATUS_META.get(self.status, {}).get("label", self.status)

    @property
    def status_badge_class(self) -> str:
        return self.STATUS_META.get(self.status, {}).get("badge", "text-bg-secondary")

    @property
    def resolved_project_name(self) -> str:
        return self.project_name or self.part_name or self.name

    @property
    def resolved_part_name(self) -> str:
        return self.part_name or self.name

    @property
    def template_profile(self):
        return self.template

    def __repr__(self) -> str:
        return f"<Project {self.resolved_part_name}>"
